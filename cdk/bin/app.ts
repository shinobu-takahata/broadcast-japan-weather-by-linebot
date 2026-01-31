#!/usr/bin/env node
import "source-map-support/register";
import * as cdk from "aws-cdk-lib";
import { WeatherBroadcastStack } from "../lib/weather-broadcast-stack";

const app = new cdk.App();
new WeatherBroadcastStack(app, "WeatherBroadcastStack", {
  env: {
    region: "ap-northeast-1",
  },
});
