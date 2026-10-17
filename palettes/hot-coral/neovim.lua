return {
  {
    "bjarneo/aether.nvim",
    branch = "v3",
    name = "aether",
    priority = 1000,
    opts = {
      colors = {
        bg = "#160d0a",
        dark_bg = "#100a08",
        darker_bg = "#0b0605",
        lighter_bg = "#251a17",

        fg = "#cec9c8",
        dark_fg = "#8e8785",
        light_fg = "#b5b0ae",
        bright_fg = "#e4e0df",
        muted = "#8c7671",

        red = "#eb817f",
        yellow = "#e6d17f",
        orange = "#f3a76b",
        green = "#b1c29a",
        cyan = "#98c2c6",
        blue = "#9da3c5",
        magenta = "#d49cb8",
        brown = "#7a5436",

        bright_red = "#f3a29e",
        bright_yellow = "#ffb19f",
        bright_green = "#ff977f",
        bright_cyan = "#b8d3d3",
        bright_blue = "#b5b5ce",
        bright_magenta = "#ff977f",

        accent = "#ff977f",
        cursor = "#e4e0df",
        foreground = "#cec9c8",
        background = "#160d0a",
        selection = "#57342b",
        selection_foreground = "#e4e0df",
        selection_background = "#57342b",
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
