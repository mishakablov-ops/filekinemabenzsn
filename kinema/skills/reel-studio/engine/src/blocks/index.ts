import { THREE_BLOCKS } from "../three";
import { BG_BLOCKS } from "./bg";
import { DATA_BLOCKS } from "./data";
import { DEV_BLOCKS } from "./dev";
import { EDITOR_BLOCKS } from "./editor";
import type { BlockDef } from "./registry";
import { SCREEN_BLOCKS } from "./screens";
import { TEXT_BLOCKS } from "./text";
import { UI_BLOCKS } from "./ui";

export const REGISTRY: Record<string, BlockDef> = {
  ...BG_BLOCKS,
  ...TEXT_BLOCKS,
  ...UI_BLOCKS,
  ...SCREEN_BLOCKS,
  ...DEV_BLOCKS,
  ...EDITOR_BLOCKS,
  ...DATA_BLOCKS,
  ...THREE_BLOCKS,
};
