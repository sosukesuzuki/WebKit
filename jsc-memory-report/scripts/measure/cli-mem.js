const isInBrowser = false;
console = { log: print };
const isD8 = false; const isSpiderMonkey = false;
if (typeof testList === "undefined") testList = undefined;
if (typeof testIterationCount === "undefined") testIterationCount = undefined;
RAMification = true;
load("./JetStreamDriver.js");
async function runJetStream() {
    try {
        await JetStream.initialize();
        await JetStream.start();
    } catch (e) { console.log("JetStream2 failed: " + e); }
    if (typeof afterRun === "function") afterRun();
}
runJetStream();
