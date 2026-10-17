return {
  {
    "bjarneo/aether.nvim",
    branch = "v3",
    name = "aether",
    priority = 1000,
    opts = {
      colors = {
        bg = "#091017",
        dark_bg = "#070c11",
        darker_bg = "#04080c",
        lighter_bg = "#171e25",

        fg = "#c8cbce",
        dark_fg = "#858a8e",
        light_fg = "#aeb1b5",
        bright_fg = "#dfe1e4",
        muted = "#707d8c",

        red = "#eb817f",
        yellow = "#e6d17f",
        orange = "#f3a76b",
        green = "#9ac8b1",
        cyan = "#81c9dc",
        blue = "#f37987",
        magenta = "#bca3cf",
        brown = "#7a5436",

        bright_red = "#f3a29e",
        bright_yellow = "#f37987",
        bright_green = "#7dbdfe",
        bright_cyan = "#a1daea",
        bright_blue = "#fa9ca4",
        bright_magenta = "#7dbdfe",

        accent = "#7dbdfe",
        cursor = "#dfe1e4",
        foreground = "#c8cbce",
        background = "#091017",
        selection = "#294058",
        selection_foreground = "#dfe1e4",
        selection_background = "#294058",
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
