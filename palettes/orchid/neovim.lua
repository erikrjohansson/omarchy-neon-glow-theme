return {
  {
    "bjarneo/aether.nvim",
    branch = "v3",
    name = "aether",
    priority = 1000,
    opts = {
      colors = {
        bg = "#130d15",
        dark_bg = "#0e0a10",
        darker_bg = "#0a060a",
        lighter_bg = "#201a23",

        fg = "#ccc9cd",
        dark_fg = "#8b878d",
        light_fg = "#b3b0b4",
        bright_fg = "#e2e0e3",
        muted = "#837787",

        red = "#eb817f",
        yellow = "#e6d17f",
        orange = "#f3a76b",
        green = "#abc2b0",
        cyan = "#92c2db",
        blue = "#97a3da",
        magenta = "#cd9cce",
        brown = "#7a5436",

        bright_red = "#f3a29e",
        bright_yellow = "#e6b1f9",
        bright_green = "#dd97f7",
        bright_cyan = "#b2d3e9",
        bright_blue = "#afb5e3",
        bright_magenta = "#dd97f7",

        accent = "#dd97f7",
        cursor = "#e2e0e3",
        foreground = "#ccc9cd",
        background = "#130d15",
        selection = "#4c3454",
        selection_foreground = "#e2e0e3",
        selection_background = "#4c3454",
      },
    },
  },
  {
    "LazyVim/LazyVim",
    opts = {
      colorscheme = "aether",
    },
  },
}
