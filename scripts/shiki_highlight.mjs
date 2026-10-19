#!/usr/bin/env node
/**
 * Read [{code, language}] JSON from stdin and emit Shiki-highlighted HTML.
 * Shiki is resolved from the cache root passed as argv[2], keeping the skill
 * archive lightweight while producing static HTML with no browser runtime.
 */
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

const root = process.argv[2];
if (!root) {
  console.error('Shiki cache root is required.');
  process.exit(2);
}

const requireFromCache = createRequire(path.join(root, 'package.json'));
const shikiPath = requireFromCache.resolve('shiki');
const { createHighlighter } = await import(pathToFileURL(shikiPath).href);
const blocks = JSON.parse(fs.readFileSync(0, 'utf8'));
// Faithful print mapping of Zed's bundled One Light syntax palette.
// Source: zed-industries/zed, assets/themes/one/one.json (One Light).
const zedOneLightTheme = {
  name: 'zed-one-light',
  type: 'light',
  colors: {
    'editor.background': '#FAFAFA',
    'editor.foreground': '#242529',
  },
  tokenColors: [
    { scope: ['comment', 'comment.line', 'comment.block', 'comment.documentation'], settings: { foreground: '#A2A3A7' } },
    { scope: ['keyword', 'storage', 'storage.type', 'keyword.control', 'keyword.operator'], settings: { foreground: '#A449AB' } },
    { scope: ['entity.name.function', 'support.function', 'meta.function-call', 'constructor'], settings: { foreground: '#5B79E3' } },
    { scope: ['entity.name.class', 'support.type', 'entity.name.type', 'storage.type'], settings: { foreground: '#3882B7' } },
    { scope: ['string', 'string.quoted'], settings: { foreground: '#649F57' } },
    { scope: ['constant.numeric', 'constant.language', 'constant.character', 'boolean'], settings: { foreground: '#AD6E25' } },
    { scope: ['variable.language', 'variable.parameter', 'entity.name.variable'], settings: { foreground: '#242529' } },
    { scope: ['property', 'variable.other.property'], settings: { foreground: '#D3604F' } },
    { scope: ['operator', 'punctuation', 'meta'], settings: { foreground: '#3882B7' } },
  ],
};
const highlighter = await createHighlighter({
  themes: [zedOneLightTheme],
  langs: [],
});

const rendered = [];
for (const { code, language } of blocks) {
  try {
    // Load per block so an unsupported language stays monochrome without
    // preventing the rest of the document from receiving Shiki highlighting.
    await highlighter.loadLanguage(language);
    const html = highlighter.codeToHtml(code, {
      lang: language,
      theme: 'zed-one-light',
    });
    // Keep Kami's parchment code surface while retaining Shiki token colors.
    rendered.push(html.replace(
      /<pre class="shiki zed-one-light"([^>]*)>/,
      (_match, attributes) => (
        '<pre class="shiki shiki-rendered zed-one-light" '
        + 'style="background-color:#FAFAFA;color:#242529"'
        + attributes.replace(/\sstyle="[^"]*"/, '')
        + '>'
      ),
    ));
  } catch (_) {
    rendered.push(null);
  }
}

highlighter.dispose();
process.stdout.write(JSON.stringify(rendered));
