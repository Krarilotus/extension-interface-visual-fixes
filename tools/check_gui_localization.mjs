import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

// Import the GUI's actual TypeScript function; Node24 strips types natively.
const { changeLocale } = await import(process.argv[2]);
const { options, locales } = JSON.parse(readFileSync(0, 'utf8'));
const original = JSON.stringify(options);
const results = [];
for (const [language, catalog] of Object.entries(locales)) {
  // Same key/value normalization as GUI readLocales; do not provide an English fallback.
  const normalized = Object.fromEntries(Object.entries(catalog).map(([k,v])=>[k.toLowerCase(),v.replaceAll('&','')]));
  const translated = changeLocale(normalized, options);
  for (let index=0;index<options.length;index++) {
    const input=options[index], output=translated[index];
    for (const field of ['text','description']) {
      const key=input[field].match(/^\s*{{(.*)}}\s*$/)[1].toLowerCase();
      assert.equal(output[field],normalized[key],`${language}/${input.name}/${field}`);
      assert.ok(!output[field].includes('{{'));
    }
    assert.deepEqual(output.category,[normalized.interface_visual_fixes]);
    assert.equal(output.url,input.url);
    assert.deepEqual(output.contents,input.contents);
    assert.equal(output.contents.value,true);
  }
  const load=translated.find(option=>option.name==='lobby_load');
  results.push({language,category:load.category[0],text:load.text,description:load.description});
  assert.equal(JSON.stringify(options),original,'Language switching must not mutate source options');
}
process.stdout.write(JSON.stringify({status:'pass',fallback:false,languages:results}));
