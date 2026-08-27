#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const TOOL_ROOT = path.join(process.env.HOME, ".codex", "tools", "next-ai-drawio-mcp-0.2.3");
const SERVER_ENTRY = path.join(
  TOOL_ROOT,
  "node_modules",
  "@next-ai-drawio",
  "mcp-server",
  "dist",
  "index.js",
);
const PNPM_ROOT = path.join(TOOL_ROOT, "node_modules", ".pnpm");
const FIG_DIR = path.join(ROOT, "paper", "figs");
const AUDIT_DIR = path.join(ROOT, "artifacts", "publication_polish");

const mx = String.raw`<mxfile host="app.diagrams.net" modified="2026-08-26T00:00:00.000Z" agent="Codex publication polish" version="24.7.17">
  <diagram id="figure1" name="Figure 1">
    <mxGraphModel dx="1400" dy="520" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1400" pageHeight="520" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>

        <mxCell id="spec-group" value="Benchmark specification (oracle-fixed)" style="rounded=1;whiteSpace=wrap;html=1;dashed=1;dashPattern=6 4;strokeColor=#8C96A3;strokeWidth=1.2;fillColor=#FAFBFC;fontColor=#2F3742;fontFamily=Helvetica;fontSize=17;fontStyle=1;verticalAlign=top;spacingTop=10;" vertex="1" parent="1">
          <mxGeometry x="20" y="40" width="350" height="450" as="geometry"/>
        </mxCell>
        <mxCell id="stakeholder" value="&lt;b&gt;Stakeholder&lt;/b&gt;&lt;br&gt;&lt;font style=&quot;font-size:15px&quot;&gt;Who bears the commitment?&lt;/font&gt;" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#7D8A99;strokeWidth=1;fillColor=#EDF1F5;fontColor=#2F3742;fontFamily=Helvetica;fontSize=18;spacing=8;" vertex="1" parent="1">
          <mxGeometry x="45" y="95" width="135" height="105" as="geometry"/>
        </mxCell>
        <mxCell id="interest" value="&lt;b&gt;Protected interest&lt;/b&gt;&lt;br&gt;&lt;font style=&quot;font-size:15px&quot;&gt;Financial, privacy,&lt;br&gt;consent, or autonomy&lt;/font&gt;" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#7D8A99;strokeWidth=1;fillColor=#EDF1F5;fontColor=#2F3742;fontFamily=Helvetica;fontSize=18;spacing=8;" vertex="1" parent="1">
          <mxGeometry x="215" y="95" width="135" height="105" as="geometry"/>
        </mxCell>
        <mxCell id="nominal" value="&lt;b&gt;Nominal endpoint&lt;/b&gt;&lt;br&gt;&lt;font style=&quot;font-size:15px&quot;&gt;State required for C&lt;sub&gt;r&lt;/sub&gt;&lt;/font&gt;" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#7D8A99;strokeWidth=1;fillColor=#FFFFFF;fontColor=#2F3742;fontFamily=Helvetica;fontSize=18;spacing=8;" vertex="1" parent="1">
          <mxGeometry x="45" y="245" width="135" height="100" as="geometry"/>
        </mxCell>
        <mxCell id="boundary" value="&lt;b&gt;Unsafe commitment&lt;/b&gt;&lt;br&gt;&lt;font style=&quot;font-size:15px&quot;&gt;Monotonic boundary for S&lt;sub&gt;r&lt;/sub&gt;&lt;/font&gt;" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#D97941;strokeWidth=1.2;fillColor=#FBEEE7;fontColor=#2F3742;fontFamily=Helvetica;fontSize=18;spacing=8;" vertex="1" parent="1">
          <mxGeometry x="215" y="245" width="135" height="100" as="geometry"/>
        </mxCell>
        <mxCell id="risk-note" value="Risk-point annotations support diagnosis only; they do not trigger safeguard delivery." style="rounded=1;whiteSpace=wrap;html=1;strokeColor=none;fillColor=#F4F6F8;fontColor=#66707C;fontFamily=Helvetica;fontSize=14;fontStyle=2;spacing=8;" vertex="1" parent="1">
          <mxGeometry x="45" y="365" width="305" height="58" as="geometry"/>
        </mxCell>

        <mxCell id="safeguard" value="&lt;b&gt;Start-of-task safeguard&lt;/b&gt;&lt;br&gt;&lt;font style=&quot;font-size:15px&quot;&gt;Fixed before first action;&lt;br&gt;task-independent wording&lt;/font&gt;" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#6F7F95;strokeWidth=1.2;fillColor=#EDF1F5;fontColor=#2F3742;fontFamily=Helvetica;fontSize=18;spacing=8;" vertex="1" parent="1">
          <mxGeometry x="420" y="105" width="185" height="115" as="geometry"/>
        </mxCell>
        <mxCell id="trajectory" value="&lt;b&gt;Observed agent trajectory&lt;/b&gt;&lt;br&gt;&lt;font style=&quot;font-size:15px&quot;&gt;Actions, browser state,&lt;br&gt;termination, and endpoint&lt;/font&gt;" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#555B66;strokeWidth=1.2;fillColor=#F4F5F6;fontColor=#2F3742;fontFamily=Helvetica;fontSize=18;spacing=8;" vertex="1" parent="1">
          <mxGeometry x="650" y="105" width="190" height="105" as="geometry"/>
        </mxCell>
        <mxCell id="evidence-label" value="Observed trajectory evidence" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=none;fillColor=none;fontColor=#555B66;fontFamily=Helvetica;fontSize=14;fontStyle=2;" vertex="1" parent="1">
          <mxGeometry x="650" y="225" width="190" height="28" as="geometry"/>
        </mxCell>

        <mxCell id="verify-group" value="Independent verification" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#8C96A3;strokeWidth=1;fillColor=#FAFBFC;fontColor=#2F3742;fontFamily=Helvetica;fontSize=17;fontStyle=1;verticalAlign=top;spacingTop=9;" vertex="1" parent="1">
          <mxGeometry x="870" y="60" width="205" height="310" as="geometry"/>
        </mxCell>
        <mxCell id="verify-c" value="&lt;b&gt;Completion verifier&lt;/b&gt;&lt;br&gt;&lt;font style=&quot;font-size:15px&quot;&gt;Endpoint evidence → C&lt;sub&gt;r&lt;/sub&gt;&lt;/font&gt;" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#4C78A8;strokeWidth=1.2;fillColor=#EAF0F6;fontColor=#2F3742;fontFamily=Helvetica;fontSize=18;spacing=8;" vertex="1" parent="1">
          <mxGeometry x="890" y="120" width="165" height="90" as="geometry"/>
        </mxCell>
        <mxCell id="verify-s" value="&lt;b&gt;Safety verifier&lt;/b&gt;&lt;br&gt;&lt;font style=&quot;font-size:15px&quot;&gt;Boundary history → S&lt;sub&gt;r&lt;/sub&gt;&lt;/font&gt;" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#D97941;strokeWidth=1.2;fillColor=#FBEEE7;fontColor=#2F3742;fontFamily=Helvetica;fontSize=18;spacing=8;" vertex="1" parent="1">
          <mxGeometry x="890" y="245" width="165" height="90" as="geometry"/>
        </mxCell>

        <mxCell id="pair" value="&lt;b&gt;Pair&lt;/b&gt;&lt;br&gt;(C&lt;sub&gt;r&lt;/sub&gt;, S&lt;sub&gt;r&lt;/sub&gt;)" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#2F3742;strokeWidth=1;fillColor=#FFFFFF;fontColor=#2F3742;fontFamily=Helvetica;fontSize=16;spacing=5;" vertex="1" parent="1">
          <mxGeometry x="1085" y="180" width="72" height="60" as="geometry"/>
        </mxCell>
        <mxCell id="matrix-anchor" value="" style="ellipse;html=1;strokeColor=none;fillColor=none;opacity=0;" vertex="1" parent="1">
          <mxGeometry x="1174" y="207" width="2" height="2" as="geometry"/>
        </mxCell>

        <mxCell id="outcome-title" value="Run-level outcome" style="rounded=0;whiteSpace=wrap;html=1;strokeColor=none;fillColor=none;fontColor=#2F3742;fontFamily=Helvetica;fontSize=18;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="1175" y="40" width="205" height="35" as="geometry"/>
        </mxCell>
        <mxCell id="q-safe-noncompletion" value="&lt;b&gt;Safe non-completion&lt;/b&gt;&lt;br&gt;C&lt;sub&gt;r&lt;/sub&gt;=0, S&lt;sub&gt;r&lt;/sub&gt;=1" style="rounded=0;whiteSpace=wrap;html=1;strokeColor=#FFFFFF;strokeWidth=1.2;fillColor=#B8C4CE;fontColor=#111111;fontFamily=Helvetica;fontSize=16;spacing=6;" vertex="1" parent="1">
          <mxGeometry x="1175" y="90" width="102.5" height="100" as="geometry"/>
        </mxCell>
        <mxCell id="q-trustworthy" value="&lt;b&gt;Trustworthy completion&lt;/b&gt;&lt;br&gt;C&lt;sub&gt;r&lt;/sub&gt;=1, S&lt;sub&gt;r&lt;/sub&gt;=1" style="rounded=0;whiteSpace=wrap;html=1;strokeColor=#FFFFFF;strokeWidth=1.2;fillColor=#4C78A8;fontColor=#FFFFFF;fontFamily=Helvetica;fontSize=16;spacing=6;" vertex="1" parent="1">
          <mxGeometry x="1277.5" y="90" width="102.5" height="100" as="geometry"/>
        </mxCell>
        <mxCell id="q-unsafe-failure" value="&lt;b&gt;Unsafe failure&lt;/b&gt;&lt;br&gt;C&lt;sub&gt;r&lt;/sub&gt;=0, S&lt;sub&gt;r&lt;/sub&gt;=0" style="rounded=0;whiteSpace=wrap;html=1;strokeColor=#FFFFFF;strokeWidth=1.2;fillColor=#555B66;fontColor=#FFFFFF;fontFamily=Helvetica;fontSize=16;spacing=6;" vertex="1" parent="1">
          <mxGeometry x="1175" y="190" width="102.5" height="100" as="geometry"/>
        </mxCell>
        <mxCell id="q-unsafe-completion" value="&lt;b&gt;Unsafe completion&lt;/b&gt;&lt;br&gt;C&lt;sub&gt;r&lt;/sub&gt;=1, S&lt;sub&gt;r&lt;/sub&gt;=0" style="rounded=0;whiteSpace=wrap;html=1;strokeColor=#FFFFFF;strokeWidth=1.2;fillColor=#D97941;fontColor=#111111;fontFamily=Helvetica;fontSize=16;spacing=6;" vertex="1" parent="1">
          <mxGeometry x="1277.5" y="190" width="102.5" height="100" as="geometry"/>
        </mxCell>
        <mxCell id="formula" value="TC_r = C_r AND S_r" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#2F3742;strokeWidth=1;fillColor=#FFFFFF;fontColor=#2F3742;fontFamily=Helvetica;fontSize=18;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="1190" y="325" width="175" height="52" as="geometry"/>
        </mxCell>
        <mxCell id="invalid" value="Infrastructure-invalid attempts remain outside the four outcome quadrants." style="rounded=1;whiteSpace=wrap;html=1;dashed=1;strokeColor=#8C96A3;strokeWidth=1;fillColor=#FFFFFF;fontColor=#66707C;fontFamily=Helvetica;fontSize=13;spacing=6;" vertex="1" parent="1">
          <mxGeometry x="1175" y="405" width="205" height="48" as="geometry"/>
        </mxCell>

        <mxCell id="e-stake-interest" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#2F3742;strokeWidth=1.4;endArrow=block;endFill=1;" edge="1" parent="1" source="stakeholder" target="interest"><mxGeometry relative="1" as="geometry"/></mxCell>
        <mxCell id="e-interest-safeguard" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#6F7F95;strokeWidth=1.4;endArrow=block;endFill=1;" edge="1" parent="1" source="interest" target="safeguard"><mxGeometry relative="1" as="geometry"/></mxCell>
        <mxCell id="e-safeguard-trajectory" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#2F3742;strokeWidth=1.5;endArrow=block;endFill=1;" edge="1" parent="1" source="safeguard" target="trajectory"><mxGeometry relative="1" as="geometry"/></mxCell>
        <mxCell id="e-trajectory-c" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#4C78A8;strokeWidth=1.5;endArrow=block;endFill=1;" edge="1" parent="1" source="trajectory" target="verify-c"><mxGeometry relative="1" as="geometry"/></mxCell>
        <mxCell id="e-trajectory-s" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;strokeColor=#D97941;strokeWidth=1.5;endArrow=block;endFill=1;" edge="1" parent="1" source="trajectory" target="verify-s"><mxGeometry relative="1" as="geometry"><Array as="points"><mxPoint x="745" y="345"/><mxPoint x="850" y="345"/><mxPoint x="850" y="283"/></Array></mxGeometry></mxCell>
        <mxCell id="e-nominal-c" value="scoring rule" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;dashed=1;dashPattern=6 4;strokeColor=#7D8A99;strokeWidth=1.1;endArrow=block;endFill=1;fontColor=#66707C;fontFamily=Helvetica;fontSize=11;" edge="1" parent="1" source="nominal" target="verify-c"><mxGeometry relative="1" as="geometry"><Array as="points"><mxPoint x="112" y="470"/><mxPoint x="830" y="470"/><mxPoint x="830" y="165"/></Array></mxGeometry></mxCell>
        <mxCell id="e-boundary-s" value="scoring rule" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;dashed=1;dashPattern=6 4;strokeColor=#D97941;strokeWidth=1.1;endArrow=block;endFill=1;fontColor=#8B5A42;fontFamily=Helvetica;fontSize=11;" edge="1" parent="1" source="boundary" target="verify-s"><mxGeometry relative="1" as="geometry"><Array as="points"><mxPoint x="282" y="440"/><mxPoint x="850" y="440"/><mxPoint x="850" y="290"/></Array></mxGeometry></mxCell>
        <mxCell id="e-c-pair" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#4C78A8;strokeWidth=1.4;endArrow=block;endFill=1;" edge="1" parent="1" source="verify-c" target="pair"><mxGeometry relative="1" as="geometry"/></mxCell>
        <mxCell id="e-s-pair" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#D97941;strokeWidth=1.4;endArrow=block;endFill=1;" edge="1" parent="1" source="verify-s" target="pair"><mxGeometry relative="1" as="geometry"/></mxCell>
        <mxCell id="e-pair-outcome" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#2F3742;strokeWidth=1.5;endArrow=block;endFill=1;" edge="1" parent="1" source="pair" target="matrix-anchor"><mxGeometry relative="1" as="geometry"/></mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>`;

async function findSdkRoot() {
  const entries = await fs.readdir(PNPM_ROOT);
  const sdkEntry = entries.find((name) => name.startsWith("@modelcontextprotocol+sdk@"));
  if (!sdkEntry) throw new Error("Installed MCP SDK was not found");
  return path.join(PNPM_ROOT, sdkEntry, "node_modules", "@modelcontextprotocol", "sdk");
}

function text(result) {
  return (result.content || []).map((item) => item.text || "").join("\n");
}

async function main() {
  await fs.mkdir(FIG_DIR, { recursive: true });
  await fs.mkdir(AUDIT_DIR, { recursive: true });
  const sdkRoot = await findSdkRoot();
  const { Client } = await import(pathToFileURL(path.join(sdkRoot, "dist", "esm", "client", "index.js")));
  const { StdioClientTransport } = await import(pathToFileURL(path.join(sdkRoot, "dist", "esm", "client", "stdio.js")));
  const transport = new StdioClientTransport({
    command: process.execPath,
    args: [SERVER_ENTRY],
    env: { ...process.env, DRAWIO_BASE_URL: "https://embed.diagrams.net" },
  });
  const client = new Client({ name: "deceptivewebbench-figure1", version: "1.0.0" });
  await client.connect(transport);
  const tools = await client.listTools();
  const toolNames = tools.tools.map((tool) => tool.name);
  for (const required of ["start_session", "create_new_diagram", "edit_diagram", "export_diagram"]) {
    if (!toolNames.includes(required)) throw new Error(`Required MCP tool missing: ${required}`);
  }

  const session = await client.callTool({ name: "start_session", arguments: {} });
  await new Promise((resolve) => setTimeout(resolve, 3500));
  const created = await client.callTool({ name: "create_new_diagram", arguments: { xml: mx } });
  const finalFormula = `<mxCell id="formula" value="TC&lt;sub&gt;r&lt;/sub&gt; = C&lt;sub&gt;r&lt;/sub&gt; ∧ S&lt;sub&gt;r&lt;/sub&gt;" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#2F3742;strokeWidth=1;fillColor=#FFFFFF;fontColor=#2F3742;fontFamily=Helvetica;fontSize=18;fontStyle=1;" vertex="1" parent="1"><mxGeometry x="1190" y="325" width="175" height="52" as="geometry"/></mxCell>`;
  const edited = await client.callTool({
    name: "edit_diagram",
    arguments: { operations: [{ operation: "update", cell_id: "formula", new_xml: finalFormula }] },
  });
  await new Promise((resolve) => setTimeout(resolve, 1800));

  const drawioPath = path.join(FIG_DIR, "trustworthy_completion_pipeline.drawio");
  const svgPath = path.join(FIG_DIR, "trustworthy_completion_pipeline.svg");
  const saved = await client.callTool({
    name: "export_diagram",
    arguments: { path: drawioPath, format: "drawio" },
  });
  const svg = await client.callTool({
    name: "export_diagram",
    arguments: { path: svgPath, format: "svg" },
  });
  await client.close();

  const drawioStat = await fs.stat(drawioPath);
  const svgStat = await fs.stat(svgPath);
  const audit = {
    package: "@next-ai-drawio/mcp-server@0.2.3",
    node: process.version,
    tools: toolNames,
    session: text(session),
    create: text(created),
    edit: text(edited),
    save: text(saved),
    svg_export: text(svg),
    outputs: {
      drawio: { path: path.relative(ROOT, drawioPath), bytes: drawioStat.size },
      svg: { path: path.relative(ROOT, svgPath), bytes: svgStat.size },
    },
    pdf_export_note: "MCP 0.2.3 supports drawio/png/svg; PDF is converted locally from the exported SVG.",
  };
  await fs.writeFile(path.join(AUDIT_DIR, "drawio_mcp_validation.json"), `${JSON.stringify(audit, null, 2)}\n`);
  console.log(JSON.stringify(audit, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
