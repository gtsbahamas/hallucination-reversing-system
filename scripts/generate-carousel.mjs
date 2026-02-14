#!/usr/bin/env node
/**
 * Generate LUCID carousel images via Gemini API directly.
 * Usage: GEMINI_API_KEY=... node scripts/generate-carousel.mjs
 */

import { writeFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';

const API_KEY = process.env.GEMINI_API_KEY;
if (!API_KEY) {
  console.error('Set GEMINI_API_KEY environment variable');
  process.exit(1);
}

const OUTPUT_DIR = join(import.meta.dirname, '..', 'docs', 'carousel');

const SLIDES = [
  {
    name: '01-hook',
    prompt: `Create a modern dark infographic slide. Large bold white text in the center reads "AI wrote code." with a line break then "Then I verified it." Below that in smaller cyan/teal text: "24 bugs found. 1 critical security vulnerability." The background is deep navy blue, almost black. No images or icons - pure typography. Clean sans-serif font like Inter or SF Pro. Subtle gradient on the background. The overall style is minimal, premium, tech-forward like Linear or Vercel marketing materials. Square 1:1 format.`,
  },
  {
    name: '02-problem',
    prompt: `Create a modern dark infographic slide with the headline "AI Hallucination is Mathematically Inevitable" in bold white text at the top. Below are three cards or badges in a row showing academic citations: "Xu et al. 2024", "Banerjee et al. 2024", "Karpowicz 2025" each with a small cyan checkmark. Below the cards in amber/gold text: "You can't train it away. You can't prompt it away." Dark charcoal background, clean sans-serif typography, minimal design. Square 1:1 format.`,
  },
  {
    name: '03-solution',
    prompt: `Create a modern dark infographic slide showing a simple horizontal three-step flow diagram. Step 1: "AI generates code" in white. Arrow pointing right. Step 2: "LUCID extracts claims" highlighted with a cyan/teal glow box. Arrow pointing right. Step 3: "Each claim verified" in white. Below the diagram in smaller text: "Not a linter. Not tests. Verification of what AI thinks is true." Dark navy background with subtle grid pattern. Glowing cyan accent on the middle step. Minimal geometric design, premium tech aesthetic. Square 1:1 format.`,
  },
  {
    name: '04-humaneval',
    prompt: `Create a modern dark data visualization slide. A large horizontal progress bar spans the width, going from 86.6% on the left (labeled "Baseline" in gray) to 100% on the right (labeled "LUCID" in glowing cyan). The 100% end glows brightly. Big bold text above the bar reads "HumanEval: Perfect Score" in white. Below the bar: "164 out of 164 problems solved. 0 errors remaining." in smaller white text. Dark navy/black background, clean minimal style, premium data visualization aesthetic. Square 1:1 format.`,
  },
  {
    name: '05-swebench',
    prompt: `Create a modern dark infographic slide with two horizontal bars comparing results. Top bar is shorter, muted gray, labeled "18.3% — Baseline". Bottom bar is significantly longer (about 1.65x), bright cyan/teal, labeled "30.3% — With LUCID". Large bold white text at top: "+65% more real-world bugs fixed". Subtitle below bars in smaller text: "300 real GitHub issues tested". Dark charcoal background, clean data visualization style, the cyan bar should glow slightly. Square 1:1 format.`,
  },
  {
    name: '06-dogfooding',
    prompt: `Create a modern dark infographic slide showing a circular flow diagram. Three nodes connected by arrows in a circle: "Claude builds LUCID" then "LUCID verifies Claude's code" then "Finds 24 bugs". In the center of the circle, bold text reads "50% issue rate". Below the circle, a red alert badge or icon with text "CRITICAL: Path traversal vulnerability". Dark navy background, red and cyan accent colors, clean typography, premium tech style. Square 1:1 format.`,
  },
  {
    name: '07-training-fails',
    prompt: `Create a modern dark infographic slide with a line graph. The x-axis shows "120 pairs", "500", "1K", "2K" as data points. The y-axis shows accuracy from about 75% to 95%. A red/orange line trends downward from 91.5% at 120 pairs declining to 77.4% at 2K pairs. Title at top in bold white: "More Training Data Made It Worse". Subtitle: "Verification must stay external — permanently." Dark background, the declining line is red/coral colored, axis labels in gray, minimal clean chart style. Square 1:1 format.`,
  },
  {
    name: '08-cta',
    prompt: `Create a modern dark infographic slide. Centered bold white text: "One line. Free for developers." Below that, a glowing cyan code box styled like a terminal/IDE showing: "npx lucid-mcp" in monospace font. Below the code box, three subtle link-style labels in a row: "GitHub" "Paper" "trylucid.dev". Dark navy background, the code box has a subtle cyan glow/border, overall minimal terminal aesthetic, premium developer-focused design. Square 1:1 format.`,
  },
];

async function generateImage(prompt, name) {
  console.log(`Generating ${name}...`);

  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateContent?key=${API_KEY}`;

  const body = {
    contents: [{
      parts: [{
        text: prompt
      }]
    }],
    generationConfig: {
      responseModalities: ["TEXT", "IMAGE"],
    }
  };

  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`Gemini API error ${response.status}: ${err}`);
  }

  const result = await response.json();

  // Extract image from response
  const parts = result.candidates?.[0]?.content?.parts || [];
  for (const part of parts) {
    if (part.inlineData) {
      const { data, mimeType } = part.inlineData;
      const ext = mimeType === 'image/png' ? 'png' : 'jpg';
      const filePath = join(OUTPUT_DIR, `${name}.${ext}`);
      await writeFile(filePath, Buffer.from(data, 'base64'));
      console.log(`  Saved: ${filePath} (${mimeType})`);
      return filePath;
    }
  }

  // If no image, log what we got
  console.error(`  No image in response for ${name}. Parts:`, parts.map(p => Object.keys(p)));
  return null;
}

async function main() {
  await mkdir(OUTPUT_DIR, { recursive: true });
  console.log(`Output directory: ${OUTPUT_DIR}`);
  console.log(`Generating ${SLIDES.length} carousel slides...\n`);

  const results = [];
  for (const slide of SLIDES) {
    try {
      const path = await generateImage(slide.prompt, slide.name);
      results.push({ name: slide.name, path, status: 'ok' });
    } catch (err) {
      console.error(`  FAILED: ${err.message}`);
      results.push({ name: slide.name, path: null, status: 'failed', error: err.message });
    }
    // Small delay between requests
    await new Promise(r => setTimeout(r, 2000));
  }

  console.log('\n=== Results ===');
  for (const r of results) {
    console.log(`${r.status === 'ok' ? 'OK' : 'FAIL'} ${r.name} → ${r.path || r.error}`);
  }
}

main().catch(err => {
  console.error('Fatal:', err);
  process.exit(1);
});
