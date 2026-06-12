"use strict";
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name2 in all)
    __defProp(target, name2, { get: all[name2], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/sveltekit/index.ts
var sveltekit_exports = {};
__export(sveltekit_exports, {
  injectSpeedInsights: () => injectSpeedInsights2
});
module.exports = __toCommonJS(sveltekit_exports);
var import_store = require("svelte/store");
var import_environment = require("$app/environment");
var import_stores = require("$app/stores");

// src/queue.ts
var initQueue = () => {
  if (window.si) return;
  window.si = function a(...params) {
    window.siq = window.siq || [];
    window.siq.push(params);
  };
};

// package.json
var name = "@vercel/speed-insights";
var version = "2.0.0";

// src/utils.ts
function isBrowser() {
  return typeof window !== "undefined";
}
function detectEnvironment() {
  try {
    const env = process.env.NODE_ENV;
    if (env === "development" || env === "test") {
      return "development";
    }
  } catch {
  }
  return "production";
}
function isDevelopment() {
  return detectEnvironment() === "development";
}
function getScriptSrc(props) {
  if (props.scriptSrc) {
    return makeAbsolute(props.scriptSrc);
  }
  if (isDevelopment()) {
    return "https://va.vercel-scripts.com/v1/speed-insights/script.debug.js";
  }
  if (props.dsn) {
    return "https://va.vercel-scripts.com/v1/speed-insights/script.js";
  }
  if (props.basePath) {
    return makeAbsolute(`${props.basePath}/speed-insights/script.js`);
  }
  return "/_vercel/speed-insights/script.js";
}
function loadProps(explicitProps, confString) {
  var _a;
  let props = explicitProps;
  if (confString) {
    try {
      props = {
        ...(_a = JSON.parse(confString)) == null ? void 0 : _a.speedInsights,
        ...explicitProps
      };
    } catch {
    }
  }
  const dataset = {
    sdkn: name + (props.framework ? `/${props.framework}` : ""),
    sdkv: version
  };
  if (props.sampleRate) {
    dataset.sampleRate = props.sampleRate.toString();
  }
  if (props.route) {
    dataset.route = props.route;
  }
  if (isDevelopment() && props.debug === false) {
    dataset.debug = "false";
  }
  if (props.dsn) {
    dataset.dsn = props.dsn;
  }
  if (props.endpoint) {
    dataset.endpoint = makeAbsolute(props.endpoint);
  } else if (props.basePath) {
    dataset.endpoint = makeAbsolute(`${props.basePath}/speed-insights/vitals`);
  }
  return {
    src: getScriptSrc(props),
    beforeSend: props.beforeSend,
    dataset
  };
}
function makeAbsolute(url) {
  return url.startsWith("http://") || url.startsWith("https://") || url.startsWith("/") ? url : `/${url}`;
}

// src/generic.ts
function injectSpeedInsights(props = {}, confString) {
  var _a;
  if (!isBrowser() || props.route === null) return null;
  initQueue();
  const { beforeSend, src, dataset } = loadProps(props, confString);
  if (document.head.querySelector(`script[src*="${src}"]`)) return null;
  if (beforeSend) {
    (_a = window.si) == null ? void 0 : _a.call(window, "beforeSend", beforeSend);
  }
  const script = document.createElement("script");
  script.src = src;
  script.defer = true;
  for (const [key, value] of Object.entries(dataset)) {
    script.dataset[key] = value;
  }
  script.onerror = () => {
    console.log(
      `[Vercel Speed Insights] Failed to load script from ${src}. Please check if any content blockers are enabled and try again.`
    );
  };
  document.head.appendChild(script);
  return {
    setRoute: (route) => {
      script.dataset.route = route ?? void 0;
    }
  };
}

// src/sveltekit/utils.ts
var import_meta = {};
function getBasePath() {
  try {
    return import_meta.env.VITE_VERCEL_OBSERVABILITY_BASEPATH;
  } catch {
  }
}
function getConfigString() {
  try {
    return import_meta.env.VITE_VERCEL_OBSERVABILITY_CLIENT_CONFIG;
  } catch {
  }
}

// src/sveltekit/index.ts
function injectSpeedInsights2(props = {}) {
  var _a;
  if (import_environment.browser) {
    const speedInsights = injectSpeedInsights(
      {
        route: (_a = (0, import_store.get)(import_stores.page).route) == null ? void 0 : _a.id,
        ...props,
        framework: "sveltekit",
        basePath: getBasePath()
      },
      getConfigString()
    );
    if (speedInsights) {
      import_stores.page.subscribe(({ route }) => {
        if (route == null ? void 0 : route.id) {
          speedInsights.setRoute(route.id);
        }
      });
    }
  }
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  injectSpeedInsights
});
//# sourceMappingURL=index.js.map