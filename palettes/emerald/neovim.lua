return {
  {
    "bjarneo/aether.nvim",
    branch = "v3",
    name = "aether",
    priority = 1000,
    opts = {
      colors = {
        bg = "#0b110a",
        dark_bg = "#080d08",
        darker_bg = "#060805",
        lighter_bg = "#191f17",

        fg = "#c9cbc8",
        dark_fg = "#868a85",
        light_fg = "#afb2ae",
        bright_fg = "#e0e2df",
        muted = "#727f6f",

        red = "#eb817f",
        yellow = "#e6d17f",
        orange = "#f3a76b",
        green = "#9bcc97",
        cyan = "#82ccc2",
        blue = "#87adc2",
        magenta = "#bda6b5",
        brown = "#7a5436",

        bright_red = "#f3a29e",
        bright_yellow = "#a2da92",
        bright_green = "#83ce6e",
        bright_cyan = "#a2ddd0",
        bright_blue = "#9fbfcb",
        bright_magenta = "#83ce6e",

        accent = "#83ce6e",
        cursor = "#e0e2df",
        foreground = "#c9cbc8",
        background = "#0b110a",
        selection = "#2d4626",
        selection_foreground = "#e0e2df",
        selection_background = "#2d4626",
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
