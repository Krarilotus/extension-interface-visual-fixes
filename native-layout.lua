-- Explicit SHC 1.41 / SHCE 1.41 layouts. See VALIDATION-EXTREME.md.
-- Chosen once at module load; no version checks enter the render path.
local extreme = data.version.isExtreme()
local function address(shc, shce) return extreme and shce or shc end
local A = {
  ProcessHeap = address(0x59E108, 0x59E10C),
  AllocateHeap = address(0x59E170, 0x59E174),
  ReallocateHeap = address(0x59E0CC, 0x59E0D0),
  PlacementEntry = address(0x5162D0, 0x516650),
  PlacementNotifyCall = address(0x516A0F, 0x516D8F),
  MinimapNotify = address(0x4B5300, 0x4B5470),
  PlacementCommandReturn = address(0x481F3C, 0x48210C),
  CameraPreviewBranch = address(0x445263, 0x445493),
  CameraPreviewExit = address(0x4467C2, 0x4469F2),
  TreeFrameLoad = address(0x4EB831, 0x4EBBC1),
  LobbyLoadDraw = address(0x42AFB2, 0x42AFE2),
  LobbyLoadAction = address(0x4426E0, 0x4428A0),
  LobbyLoadReject = address(0x442693, 0x442853),
  LobbyPrepare = address(0x42733A, 0x4273BA),
  TowerDoorCall1 = address(0x4E3681, 0x4E3A11),
  TowerDoorCall2 = address(0x4E36D1, 0x4E3A61),
  TowerDoorCall3 = address(0x4E3724, 0x4E3AB4),
  TowerDoorCall4 = address(0x4E3777, 0x4E3B07),
  TowerDoorCall5 = address(0x4E3807, 0x4E3B97),
  RenderMapEntry = address(0x4E8CF0, 0x4E9080),
  RenderMapResume = address(0x4E8CF8, 0x4E9088),
  FoundationDrawCall = address(0x4EBA52, 0x4EBDE2),
  BuildingRefresh = address(0x41B7FF, 0x41B80F),
  BuildingRefreshResume = address(0x41B806, 0x41B816),
  BuildingRefreshTile = address(0x41B855, 0x41B865),
  BuildingRefreshTileResume = address(0x41B85C, 0x41B86C),
  MapReset = address(0x512450, 0x5127D0),
  MapResetResume = address(0x512456, 0x5127D6),
  TowerFoundationSelect = address(0x50EDAF, 0x50F12F),
  TowerFoundationOriginal = address(0x50EDB5, 0x50F135),
  TowerFoundationResume = address(0x50EE19, 0x50F199),
  DrawBuildingOverlay = address(0x455300, 0x455530),
  DrawCliff = address(0x453B00, 0x453D30),
  CliffSelector = address(0x4FC95C, 0x4FCCDC),
  CliffSelectorFallback = address(0x4FC9B9, 0x4FCD39),
  CliffSelectorReturn = address(0x4FC9C0, 0x4FCD40),
  CliffSource = address(0x453BDB, 0x453E0B),
  CliffOffsetSource = address(0x45417B, 0x4543AB),
  LobbyLoadItem = address(0x5E9988, 0x5E9848),
  LobbyLoadX = address(0x5E998C, 0x5E984C),
  LobbyLoadY = address(0x5E9990, 0x5E9850),
  LobbyLoadActive = address(0x5E99A0, 0x5E9860),
  LobbyLoadTexture = address(0x5E99A8, 0x5E9868),
  LobbyLoadTextureFrame = address(0x5E99AC, 0x5E986C),
  LobbyLoadTooltip = address(0x5E99B4, 0x5E9874),
  ImageHeaders = address(0xB98790, 0xB98930),
  ImageSizes = address(0xC9A590, 0xC9A730),
  ImageOffsets = address(0xD0BA10, 0xD0BBB0),
  CliffImages = address(0xD7CEB4, 0xD7D054),
  WallImages = address(0xD7CEB8, 0xD7D058),
  TowerImages = address(0xD7CF68, 0xD7D108),
  OverlayVerticalOffset = address(0xED3158, 0xED35D8),
  SecondaryImage = address(0xED316C, 0xED35EC),
  PrimaryImage = address(0xED3174, 0xED35F4),
  CliffWidth = address(0xED3178, 0xED35F8),
  CliffFace = address(0xED317C, 0xED35FC),
  OverlayGm = address(0xED3180, 0xED3600),
  RenderMapState = address(0xF98394, 0xF98814),
  Buildings = address(0xF98534, 0xF989B4),
  BuildingKind = address(0xF98606, 0xF98A86),
  BuildingId = address(0xF9860C, 0xF98A8C),
  BuildingX = address(0xF98622, 0xF98AA2),
  BuildingY = address(0xF98624, 0xF98AA4),
  BuildingTile = address(0xF98628, 0xF98AA8),
  BuildingState = address(0xF9862C, 0xF98AAC),
  CameraScrolling = address(0x112B070, 0x112B4F0),
  LobbyMode = address(0x191DD80, 0x2354DF0),
  TileLogic = address(0x1BF8368, 0x268B868),
  TileBuilding = address(0x1C95BB8, 0x27290B8),
  TileHeight = address(0x1D32C38, 0x27C6138),
  TileTerrain = address(0x1D46648, 0x27D9B48),
  MapOrientation = address(0x1FE7AA4, 0x2A7AFA4),
  GameMode = address(0x1FE7D78, 0x2A7B278),
  TextureRenderer = address(0x1FEA090, 0x2A7D590),
  ImageData = address(0x1FEA108, 0x2A7D608),
  CurrentBuildingLayerPointer = address(0x21AEC4C, 0x2C4214C),
  MapWidth = address(0x21AEC54, 0x2C42154),
  TileRows = address(0x2337300, 0x2DCA800),
  PreviewWidth = address(0x1FE7AF0, 0x2A7AFF0),
  LeftHeld = address(0xF2C9F0, 0xF2CE70),
  LeftReleased = address(0xF2C9D8, 0xF2CE58),
  LocalPlayer = address(0x1A275DC, 0x24BAADC),
  TreeFrame = address(0xF2CC54, 0xF2D0D4),
  TreeStage = address(0xF2CCD4, 0xF2D154),
  TreeFelling = address(0xF2CCCA, 0xF2D14A),
  TreeKind = address(0xF2CC9A, 0xF2D11A),
}
local M = {addresses = A}
-- UCP 3.0.7 gives FASM a 64 KB workspace. Expand only referenced operands:
-- declaring the entire address table for every wrapper exhausts that budget.
local function operands(script)
  return (script:gsub("[%a_][%w_]*", function(name)
    return A[name] and string.format("0x%X", A[name]) or name
  end))
end
function M.allocateAssembly(script)
  return core.allocateAssembly(operands(script))
end
function M.assemble(script, origin)
  return core.assemble(operands(script), nil, origin)
end
M.patterns = {
  CameraPreview = extreme and "39 1D F0 B4 12 01 0F 85 59 15 00 00 8B 3D E0 20 C4 02"
    or "39 1D 70 B0 12 01 0F 85 59 15 00 00 8B 3D E0 EB 1A 02",
  TreeFrameLoad = extreme and "69 F6 9C 00 00 00 0F BF 86 D8 D0 F2 00 85 C0 8B 96 D4 D0 F2 00 8B 0C 85 30 D0 D7 00"
    or "69 F6 9C 00 00 00 0F BF 86 58 CC F2 00 85 C0 8B 96 54 CC F2 00 8B 0C 85 90 CE D7 00",
  TowerDoorCall1 = extreme and "DC 52 50 6A 36 B9 90 D5 A7 02 E8 1A 1B F7 FF"
    or "DC 52 50 6A 36 B9 90 A0 FE 01 E8 7A 1C F7 FF",
  TowerDoorCall2 = extreme and "DC 52 50 6A 36 B9 90 D5 A7 02 E8 CA 1A F7 FF"
    or "DC 52 50 6A 36 B9 90 A0 FE 01 E8 2A 1C F7 FF",
  TowerDoorCall3 = extreme and "CC 52 50 6A 36 B9 90 D5 A7 02 E8 77 1A F7 FF"
    or "CC 52 50 6A 36 B9 90 A0 FE 01 E8 D7 1B F7 FF",
  TowerDoorCall4 = extreme and "CD 52 50 6A 36 B9 90 D5 A7 02 E8 24 1A F7 FF"
    or "CD 52 50 6A 36 B9 90 A0 FE 01 E8 84 1B F7 FF",
  TowerDoorCall5 = extreme and "03 D5 52 51 50 B9 90 D5 A7 02 E8 94 19 F7 FF"
    or "03 D5 52 51 50 B9 90 A0 FE 01 E8 F4 1A F7 FF",
  FoundationDrawCall = extreme and "E8 49 7F F6 FF 83 7C 24 54 00 74 34"
    or "E8 A9 80 F6 FF 83 7C 24 54 00 74 34",
  BuildingRefreshTile = extreme and "03 81 28 E0 18 00 8B 04 85 68 B8 68 02 A9 00 01 00 00 74 1C A8 02 75 18 A9"
    or "03 81 28 E0 18 00 8B 04 85 68 83 BF 01 A9 00 01 00 00 74 1C A8 02 75 18 A9",
  MapReset = extreme and "51 A1 54 21 C4 02 53 55 8B 2D 50 21 C4 02 56 89 44 24 0C"
    or "51 A1 54 EC 1A 02 53 55 8B 2D 50 EC 1A 02 56 89 44 24 0C",
  TowerFoundationSelect = extreme and "66 89 84 51 E0 80 0C 00 EB 6A 8B 95 1C FF FF FF 8B 82 08 49 55 00 8B 0D 54 D0 D7 00 8D 54 01 FF"
    or "66 89 84 51 E0 80 0C 00 EB 6A 8B 95 1C FF FF FF 8B 82 08 49 55 00 8B 0D B4 CE D7 00 8D 54 01 FF",
  LobbyPrepare = extreme and "C7 05 78 B2 A7 02 03 00 00 00 89 35 AC D1 A7 02 89 35 B4 B2 A7 02"
    or "C7 05 78 7D FE 01 03 00 00 00 89 35 AC 9C FE 01 89 35 B4 7D FE 01",
  RenderMapEntry = extreme and "83 EC 64 A1 14 88 F9 00 53 55 56 8B D9 57 33 FF 33 F6"
    or "83 EC 64 A1 94 83 F9 00 53 55 56 8B D9 57 33 FF 33 F6",
  CliffSource = extreme and "A1 F4 35 ED 00 8B 14 85 B0 BB D0 00 01 55 F0 A1 EC 35 ED 00 8B 14 85 B0 BB D0 00 01 55 F8"
    or "A1 74 31 ED 00 8B 14 85 10 BA D0 00 01 55 F0 A1 6C 31 ED 00 8B 14 85 10 BA D0 00 01 55 F8",
  CliffOffsetSource = extreme and "8B 15 F4 35 ED 00 8B 04 95 B0 BB D0 00 01 45 EC 8B 15 EC 35 ED 00 8B 04 95 B0 BB D0 00 01 45 FC"
    or "8B 15 74 31 ED 00 8B 04 95 10 BA D0 00 01 45 EC 8B 15 6C 31 ED 00 8B 04 95 10 BA D0 00 01 45 FC",
}
return M
