local active_border_color = { colors = { "rgba(954f5aee)", "rgba(4f78a2ee)" }, angle = 45 }
local inactive_border_color = "rgba(2f4963ee)"

hl.config({
  general = {
    col = {
      active_border = active_border_color,
      inactive_border = inactive_border_color,
    },
  },

  group = {
    col = {
      border_active = active_border_color,
      border_inactive = inactive_border_color,
    },
  },
})
