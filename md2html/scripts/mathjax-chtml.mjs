import readline from 'node:readline';
import {createRequire} from 'node:module';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const FONT_URL = 'mathjax/woff2';

function message(error) {
  return error && error.stack ? error.stack : String(error);
}

let MathJax;
let adaptor;
try {
  const nodeModules = path.resolve(process.argv[2]);
  const require = createRequire(pathToFileURL(path.join(nodeModules, 'package.json')));
  MathJax = (await import(pathToFileURL(require.resolve('mathjax')).href)).default;
  await MathJax.init({
    loader: {
      load: ['input/tex', 'output/chtml', '[mathjax-tex]/chtml'],
      paths: {'mathjax-tex': '@mathjax/mathjax-tex-font'}
    },
    chtml: {fontURL: FONT_URL, linebreaks: {inline: false}, scale: 1.195}
  });
  adaptor = MathJax.startup.adaptor;
  const fontFile = pathToFileURL(require.resolve('@mathjax/mathjax-tex-font/chtml/woff2/mjx-tex-n.woff2'));
  console.log(JSON.stringify({
    ready: true,
    css: adaptor.outerHTML(MathJax.chtmlStylesheet()),
    fontDir: fileURLToPath(new URL('.', fontFile))
  }));
} catch (error) {
  console.log(JSON.stringify({ready: false, error: message(error)}));
  process.exit(1);
}

const lines = readline.createInterface({input: process.stdin, crlfDelay: Infinity});
for await (const line of lines) {
  if (!line.trim()) continue;
  try {
    const request = JSON.parse(line);
    const node = MathJax.tex2chtml(request.tex, {display: Boolean(request.display)});
    const html = adaptor.outerHTML(node).replace(/\sdata-latex="[^"]*"/g, '');
    console.log(JSON.stringify({
      ok: true,
      html,
      css: adaptor.outerHTML(MathJax.chtmlStylesheet())
    }));
  } catch (error) {
    console.log(JSON.stringify({ok: false, error: message(error)}));
  }
}
