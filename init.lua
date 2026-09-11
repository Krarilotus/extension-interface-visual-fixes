local enabled = false

return {
  enable = function(self, config)
    if enabled then return end
    if config["lobby-map-descriptions"] == true then
      require("lobby-description").enable()
    end
    if config["lobby-load"] == true then
      require("lobby-load").enable()
    end
    enabled = true
  end,
  disable = function()
    error("Interface and Visual Fixes requires a game restart to disable")
  end,
}
