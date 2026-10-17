return {
  {
    "bjarneo/aether.nvim",
    branch = "v3",
    name = "aether",
    priority = 1000,
    opts = {
      colors = {
        bg = "#061214",
        dark_bg = "#040e0f",
        darker_bg = "#03090a",
        lighter_bg = "#131f22",

        fg = "#c7cbcc",
        dark_fg = "#838a8c",
        light_fg = "#adb2b3",
        bright_fg = "#dee2e3",
        muted = "#698186",

        red = "#eb817f",
        yellow = "#e6d17f",
        orange = "#f3a76b",
        green = "#85cbad",
        cyan = "#6cccd9",
        blue = "#e37cbf",
        magenta = "#a7a6cb",
        brown = "#7a5436",

        bright_red = "#f3a29e",
        bright_yellow = "#e37cbf",
        bright_green = "#0acde9",
        bright_cyan = "#8cdde7",
        bright_blue = "#ec9dcf",
        bright_magenta = "#0acde9",

        accent = "#0acde9",
        cursor = "#dee2e3",
        foreground = "#c7cbcc",
        background = "#061214",
        selection = "#074650",
        selection_foreground = "#dee2e3",
        selection_background = "#074650",
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
