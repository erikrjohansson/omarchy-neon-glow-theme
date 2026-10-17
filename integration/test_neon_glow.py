"""Exercise selection, theme isolation, restart persistence, and failed refresh recovery."""
import colorsys
import importlib.util
import json
import multiprocessing
from pathlib import Path
import queue
import re
import shutil
import tempfile
import time
import tomllib
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('neon_glow',ROOT/'integration/neon_glow.py')
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)

class FollowerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.home=Path(self.temp.name)
        self.runtime=self.home/'runtime'; self.runtime.mkdir()
        self.current=self.home/'.local/state/omarchy/current'
        (self.current/'theme').mkdir(parents=True)
        (self.current/'theme.name').write_text('neon-glow\n')
        self.calls=[]
        self.follower=module.Follower(home=self.home,root=ROOT,runtime=self.runtime,runner=lambda command: self.calls.append(command) or True)
    def tearDown(self): self.temp.cleanup()
    def select(self,slug,design=0):
        link=self.current/'background'; link.unlink(missing_ok=True)
        link.symlink_to(ROOT/'backgrounds'/self.follower.manifest[slug]['backgrounds'][design])
    def test_all_palettes_and_designs(self):
        for slug in self.follower.manifest:
            self.select(slug)
            self.assertTrue(self.follower.apply())
            self.assertTrue(self.follower.matches(slug))
            # A logo wallpaper from before the wordmark-only update keeps its palette.
            count=len(self.calls)
            logo=self.home/self.follower.manifest[slug]['backgrounds'][0].replace('-wordmark-','-logo-')
            logo.touch(); link=self.current/'background'; link.unlink(); link.symlink_to(logo)
            self.assertEqual(self.follower.desired()[0],slug)
            self.assertFalse(self.follower.apply())
            self.assertEqual(count,len(self.calls))
    def test_other_theme_is_untouched(self):
        self.select('red-white-blue'); (self.current/'theme.name').write_text('other')
        self.assertFalse(self.follower.apply()); self.assertEqual(self.calls,[])
        self.assertFalse((self.current/'theme/colors.toml').exists())
    def test_restart_and_reapply(self):
        self.select('orchid'); self.follower.apply()
        replacement=module.Follower(home=self.home,root=ROOT,runtime=self.runtime,runner=lambda command: True)
        self.assertEqual(replacement.desired()[0],'orchid')
        self.assertFalse(replacement.apply())
        (self.current/'theme/colors.toml').write_text((ROOT/'colors.toml').read_text())
        self.assertTrue(replacement.apply())
        self.assertEqual(json.loads(replacement.saved.read_text())['variant'],'orchid')
    def test_missing_or_unknown_wallpaper(self):
        self.assertFalse(self.follower.apply())
        (self.home/'custom.png').touch(); (self.current/'background').symlink_to(self.home/'custom.png')
        self.assertFalse(self.follower.apply()); self.assertEqual(self.calls,[])
    def test_legacy_wallpaper_names_after_update(self):
        for slug, item in self.follower.manifest.items():
            for name in item['backgrounds']:
                legacy = name.replace('-4k.png', '-no-floor-4k.png').replace('12-red-white-blue-', '12-us-')
                wallpaper = self.home/legacy
                wallpaper.touch()
                link = self.current/'background'
                link.unlink(missing_ok=True)
                link.symlink_to(wallpaper)
                self.assertEqual(self.follower.desired()[0], slug)
                self.follower.apply()
                self.assertTrue(self.follower.matches(slug))
    def test_removed_sets_fall_back(self):
        for name, slug in (('04-blue-logo-4k.png','cyberpunk'),('08-ultraviolet-wordmark-4k.png','orchid'),
                           ('11-vaporwave-logo-no-floor-4k.png','orchid'),
                           ('05-blue-yellow-wordmark-4k.png','red-white-blue'),
                           ('10-ruby-red-wordmark-4k.png','hot-coral'),
                           ('09-cyberpunk-wordmark-4k.png','cyberpunk')):
            wallpaper = self.home/name
            wallpaper.touch()
            link = self.current/'background'
            link.unlink(missing_ok=True)
            link.symlink_to(wallpaper)
            self.assertEqual(self.follower.desired()[0], slug, name)
    def test_selection_changed_while_waiting_for_lock(self):
        self.select('gold')
        original=self.follower.desired
        count=0
        def desired():
            nonlocal count
            count+=1
            if count==2: (self.current/'theme.name').write_text('other')
            return original()
        self.follower.desired=desired
        self.assertFalse(self.follower.apply()); self.assertEqual(self.calls,[])
    def test_shell_failure_is_retried(self):
        self.select('red-white-blue'); self.follower.runner=lambda command: False
        self.assertFalse(self.follower.apply()); self.assertFalse(self.follower.matches('red-white-blue'))
        self.follower.runner=lambda command: True
        self.assertTrue(self.follower.apply())

    def start_watcher(self, shell_ready=True):
        ready = self.home/'shell-ready'
        if shell_ready: ready.touch()
        context = multiprocessing.get_context('fork')
        self.events = context.Queue()
        def follow():
            self.follower.runner = lambda command: ready.exists()
            original = self.follower.apply
            def apply():
                result = original()
                choice = self.follower.desired()
                self.events.put((choice, bool(choice and self.follower.matches(choice[0]))))
                return result
            self.follower.apply = apply
            self.follower.watch()
        process = context.Process(target=follow)
        process.start()
        def stop():
            process.terminate()
            process.join(3)
            if process.is_alive():
                process.kill()
                process.join()
            self.events.close()
        self.addCleanup(stop)

    def await_palette(self, slug, matched=True):
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            try:
                choice, actual = self.events.get(timeout=max(.01, deadline-time.monotonic()))
            except queue.Empty:
                break
            if (choice[0] if choice else None) == slug and actual == matched:
                return
        self.fail(f'Watcher did not reach {slug}, matched={matched}')

    def assert_watcher_sleeps(self):
        # Allow notifications from its own palette writes to settle, then prove
        # apply() is not called repeatedly as it was in the polling loop.
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            try:
                self.events.get(timeout=.8)
            except queue.Empty:
                with self.assertRaises(queue.Empty): self.events.get(timeout=1)
                return
        self.fail('Watcher keeps waking while idle')

    def test_notifications_switch_away_back_and_idle(self):
        self.select('gold')
        (self.current/'theme.name').write_text('other')
        self.start_watcher()
        self.await_palette(None, False)
        self.assert_watcher_sleeps()
        self.assertFalse((self.current/'theme/colors.toml').exists())
        # Atomic replacement of theme.name must also wake the watcher.
        replacement = self.current/'new-name'
        replacement.write_text('neon-glow')
        replacement.replace(self.current/'theme.name')
        self.await_palette('gold')
        self.assert_watcher_sleeps()
        self.select('hot-coral')
        self.await_palette('hot-coral')
        (self.current/'theme.name').write_text('other')
        self.await_palette(None, False)
        before = (self.current/'theme/colors.toml').read_bytes()
        self.select('gold')
        self.await_palette(None, False)
        self.assert_watcher_sleeps()
        self.assertEqual(before, (self.current/'theme/colors.toml').read_bytes())
        (self.current/'theme.name').write_text('neon-glow')
        self.await_palette('gold')

    def test_notifications_replaced_theme_and_config(self):
        self.select('cyberpunk')
        self.start_watcher()
        self.await_palette('cyberpunk')
        replacement = self.current/'next-theme'
        replacement.mkdir()
        shutil.rmtree(self.current/'theme')
        replacement.rename(self.current/'theme')
        self.await_palette('cyberpunk')
        self.assert_watcher_sleeps()
        (self.current/'theme/colors.toml').write_text('replaced')
        self.await_palette('cyberpunk')
        self.assertNotEqual((self.current/'theme/colors.toml').read_text(), 'replaced')

    def test_notifications_retry_without_external_change(self):
        self.select('red-white-blue')
        self.start_watcher(shell_ready=False)
        self.await_palette('red-white-blue', False)
        # No watched file changes: a timed retry must recover on its own.
        (self.home/'shell-ready').touch()
        self.await_palette('red-white-blue')
        self.assert_watcher_sleeps()
    def test_valid_configs_and_contrast(self):
        def lum(color):
            channels=[int(color[i:i+2],16)/255 for i in (1,3,5)]
            channels=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in channels]
            return sum(a*b for a,b in zip(channels,(.2126,.7152,.0722)))
        for slug in self.follower.manifest:
            palette=ROOT/'palettes'/slug
            for p in palette.glob('*.toml'): tomllib.loads(p.read_text())
            for p in palette.glob('*.json'): json.loads(p.read_text())
            colors=tomllib.loads((palette/'colors.toml').read_text())
            self.assertLess(lum(colors['background']),.01,(slug,'background'))
            self.assertLessEqual(lum(colors['dark_background']),lum(colors['background']),(slug,'sidebar'))
            slots=('red','green','yellow','blue','magenta','cyan','bright_red','bright_green','bright_yellow','bright_blue','bright_magenta','bright_cyan')
            def hsv(color):
                return colorsys.rgb_to_hsv(*(int(color[i:i+2],16)/255 for i in (1,3,5)))
            # Readable text is near-neutral; the accent owns one terminal slot.
            self.assertLess(hsv(colors['foreground'])[1],.12,(slug,'foreground'))
            if hsv(colors['accent'])[1]>.25:
                self.assertIn(colors['accent'],[colors[s] for s in (*slots,'orange')],slug)
            # Errors stay red. Only the palette's own colours are strong; the
            # other slots are soft tints, but none may turn grey or white.
            red_hue=hsv(colors['red'])[0]
            self.assertLess(min(red_hue,1-red_hue),.05,(slug,'red'))
            for slot in slots:
                self.assertGreater(hsv(colors[slot])[1],.04 if slot.startswith('bright_') else .08,(slug,slot))
            for key in ('foreground','accent','muted',*slots):
                ratio=(lum(colors[key])+.05)/(lum(colors['background'])+.05)
                self.assertGreaterEqual(ratio,4.5,(slug,key,ratio))
            gtk=dict(re.findall(r'@define-color (\w+) (#[0-9a-fA-F]{6});',(palette/'gtk.css').read_text()))
            ratio=(lum(gtk['foreground'])+.05)/(lum(gtk['error_red'])+.05)
            self.assertGreaterEqual(ratio,4.5,(slug,'destructive button',ratio))
            lock=tomllib.loads((palette/'shell.lock.toml').read_text())['lock']
            self.assertLess(lum(lock['placeholder']),lum(lock['text']),(slug,'lock placeholder'))
            for p in palette.iterdir():
                self.assertNotIn('{{ ',p.read_text(),p.name)

if __name__=='__main__': unittest.main()
