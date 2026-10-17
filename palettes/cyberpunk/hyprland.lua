local active_border_color = { colors = { "rgba(8b527bee)", "rgba(088294ee)" }, angle = 45 }
local inactive_border_color = "rgba(074e58ee)"

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
