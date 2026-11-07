#!/usr/bin/env node
// SR-RX polkit rule harness (CI model, not a polkitd run): evaluates every staged polkit rule
// against the decision cases of deployment/tests/polkit_cases/*.json, the way polkitd 124 does:
//  - all *.rules files of <root>/etc/polkit-1/rules.d and <root>/usr/share/polkit-1/rules.d are
//    loaded, sorted by file name, a name present in both in /etc order first
//    (src/polkitbackend/polkitbackendcommon.c:453-477, polkitbackendduktapeauthority.c:112-143);
//  - the functions given to polkit.addRule() run in that order and the first truthy result wins;
//    none is "not_handled", i.e. the action's own default policy decides (src/polkitbackend/init.js);
//  - action.lookup(key) returns the detail key, subject.user / subject.groups / isInGroup().
// Usage: node harness.js (--root ROOTFS | --rules-dir DIR ...) CASES.json ...
// Exit 0 only when every case gets its expected decision and every required rule file is present.
"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const RESULTS = { NO: "no", YES: "yes", AUTH_SELF: "auth_self", AUTH_SELF_KEEP: "auth_self_keep",
                  AUTH_ADMIN: "auth_admin", AUTH_ADMIN_KEEP: "auth_admin_keep", NOT_HANDLED: null };
const EXPECTED = new Set(["yes", "no", "auth_self", "auth_self_keep", "auth_admin", "auth_admin_keep", "not_handled"]);

function fail(message) {
  process.stderr.write("polkit harness: " + message + "\n");
  process.exit(2);
}

function parseArgs(argv) {
  const dirs = [], cases = [];
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--root") {
      const root = argv[++i];
      if (!root) fail("--root needs a directory");
      dirs.push(path.join(root, "etc/polkit-1/rules.d"), path.join(root, "usr/share/polkit-1/rules.d"));
    } else if (argv[i] === "--rules-dir") {
      if (!argv[i + 1]) fail("--rules-dir needs a directory");
      dirs.push(argv[++i]);
    } else {
      cases.push(argv[i]);
    }
  }
  if (!dirs.length || !cases.length) fail("usage: harness.js (--root ROOTFS | --rules-dir DIR ...) CASES.json ...");
  return { dirs, cases };
}

function ruleFiles(dirs) {
  const files = [];
  for (const dir of dirs) {
    let names = [];
    try {
      names = fs.readdirSync(dir);
    } catch (error) {
      continue; // polkitd logs a missing directory and goes on
    }
    for (const name of names) {
      if (name.endsWith(".rules")) files.push(path.join(dir, name));
    }
  }
  const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);
  files.sort((a, b) => cmp(path.basename(a), path.basename(b)) || cmp(a, b));
  return files;
}

function loadRules(files) {
  const functions = [];
  const polkit = {
    Result: Object.freeze(Object.assign({}, RESULTS)),
    addRule: (callback) => {
      if (typeof callback !== "function") throw new Error("addRule needs a function");
      functions.push(callback);
    },
    addAdminRule: () => {}, // admin identities do not change a decision for these subjects
    log: () => {},
    spawn: () => { throw new Error("polkit.spawn is not available in the harness"); },
  };
  for (const file of files) {
    const context = vm.createContext({ polkit });
    try {
      vm.runInContext(fs.readFileSync(file, "utf8"), context, { filename: file, timeout: 1000 });
    } catch (error) {
      fail("rule file does not load: " + file + ": " + error.message);
    }
  }
  return functions;
}

function makeAction(id, details) {
  const action = { id };
  for (const key of Object.keys(details || {})) action["_detail_" + key] = String(details[key]);
  action.lookup = function (name) { return this["_detail_" + name]; };
  return action;
}

function makeSubject(spec) {
  const groups = Array.isArray(spec.groups) ? spec.groups.slice() : [spec.user];
  return { user: spec.user, groups, pid: 4242, seat: "", session: "", local: spec.local === true,
           active: spec.active === true, isInGroup: (group) => groups.indexOf(group) >= 0,
           isInNetGroup: () => false };
}

function decide(functions, testCase) {
  const action = makeAction(testCase.action, testCase.details);
  const subject = makeSubject(testCase);
  for (const fn of functions) {
    const value = fn(action, subject);
    if (value) return value;
  }
  return "not_handled";
}

function main() {
  const { dirs, cases } = parseArgs(process.argv.slice(2));
  const files = ruleFiles(dirs);
  const names = new Set(files.map((file) => path.basename(file)));
  const functions = loadRules(files);
  let failures = 0, total = 0;
  process.stdout.write("rules (" + files.length + "): " + files.map((f) => path.basename(f)).join(", ") + "\n");
  for (const casePath of cases) {
    let document;
    try {
      document = JSON.parse(fs.readFileSync(casePath, "utf8"));
    } catch (error) {
      fail("case file does not parse: " + casePath + ": " + error.message);
    }
    if (document.schema_version !== 1 || document.kind !== "srrx_polkit_cases" || !Array.isArray(document.cases)
        || !document.cases.length || !Array.isArray(document.requires)) {
      fail("not an srrx_polkit_cases v1 file with cases and requires: " + casePath);
    }
    for (const required of document.requires) {
      total++;
      if (!names.has(required)) {
        process.stdout.write("FAIL " + path.basename(casePath) + ": required rule file not staged: " + required + "\n");
        failures++;
      }
    }
    for (const testCase of document.cases) {
      total++;
      if (typeof testCase.name !== "string" || typeof testCase.action !== "string" || typeof testCase.user !== "string"
          || !EXPECTED.has(testCase.expect)) {
        fail("malformed case in " + casePath + ": " + JSON.stringify(testCase).slice(0, 200));
      }
      const got = decide(functions, testCase);
      const ok = got === testCase.expect;
      if (!ok) failures++;
      process.stdout.write((ok ? "PASS " : "FAIL ") + path.basename(casePath) + ": " + testCase.name + " -> " + got
                           + (ok ? "" : " (expected " + testCase.expect + ")") + "\n");
    }
  }
  process.stdout.write("polkit harness (CI model): " + (total - failures) + "/" + total + " cases as expected\n");
  process.exit(failures ? 1 : 0);
}

main();
