#!/usr/bin/env node

// Export the hand-edited Figure 1 Draw.io source without replacing it.

import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const TOOL_ROOT = path.join(process.env.HOME, ".codex", "tools", "next-ai-drawio-mcp-0.2.3");
const SERVER_ENTRY = path.join(TOOL_ROOT, "node_modules", "@next-ai-drawio", "mcp-server", "dist", "index.js");
const PNPM_ROOT = path.join(TOOL_ROOT, "node_modules", ".pnpm");
const DRAWIO = path.join(ROOT, "paper", "figs", "Figure 1.drawio");
const SVG = path.join(ROOT, "paper", "figs", "figure1.svg");
const AUDIT = path.join(ROOT, "artifacts", "publication_polish", "drawio_figure1_validation.json");

async function findSdkRoot() {
  const entries = await fs.readdir(PNPM_ROOT);
  const sdkEntry = entries.find((name) => name.startsWith("@modelcontextprotocol+sdk@"));
  if (!sdkEntry) throw new Error("Installed MCP SDK was not found");
  return path.join(PNPM_ROOT, sdkEntry, "node_modules", "@modelcontextprotocol", "sdk");
}

function resultText(result) {
  return (result.content || []).map((item) => item.text || "").join("\n");
}

async function main() {
  const source = await fs.readFile(DRAWIO, "utf8");
  const sdkRoot = await findSdkRoot();
  const { Client } = await import(pathToFileURL(path.join(sdkRoot, "dist", "esm", "client", "index.js")));
  const { StdioClientTransport } = await import(pathToFileURL(path.join(sdkRoot, "dist", "esm", "client", "stdio.js")));
  const transport = new StdioClientTransport({
    command: process.execPath,
    args: [SERVER_ENTRY],
    env: { ...process.env, DRAWIO_BASE_URL: "https://embed.diagrams.net" },
  });
  const client = new Client({ name: "deceptivewebbench-figure1-export", version: "1.0.0" });
  await client.connect(transport);
  const available = (await client.listTools()).tools.map((tool) => tool.name);
  for (const required of ["start_session", "create_new_diagram", "export_diagram"]) {
    if (!available.includes(required)) throw new Error(`Required MCP tool missing: ${required}`);
  }
  const session = await client.callTool({ name: "start_session", arguments: {} });
  await new Promise((resolve) => setTimeout(resolve, 3000));
  const created = await client.callTool({ name: "create_new_diagram", arguments: { xml: source } });
  const svg = await client.callTool({ name: "export_diagram", arguments: { path: SVG, format: "svg" } });
  await client.close();
  const report = {
    package: "@next-ai-drawio/mcp-server@0.2.3",
    node: process.version,
    canonical_source: path.relative(ROOT, DRAWIO),
    session: resultText(session),
    create: resultText(created),
    svg_export: resultText(svg),
    output: path.relative(ROOT, SVG),
  };
  await fs.writeFile(AUDIT, `${JSON.stringify(report, null, 2)}\n`);
  console.log(JSON.stringify(report, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
