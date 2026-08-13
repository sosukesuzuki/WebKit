// Module runner for 16 (importValue) so the ShadowRealm's relative import has a file referrer.
globalThis.print = (...a) => console.log(a.map(String).join(" "));
await import(process.argv[2]);
