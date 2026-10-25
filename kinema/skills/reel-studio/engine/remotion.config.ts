import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setJpegQuality(95);
Config.setChromiumOpenGlRenderer("angle");
Config.setConcurrency(6);
Config.setCodec("h264");
Config.setCrf(16);
Config.setPixelFormat("yuv420p");
Config.setAudioBitrate("320k");
Config.setOverwriteOutput(true);
Config.setColorSpace("bt709");
