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

// src/nuxt/runtime/index.ts
var runtime_exports = {};
__export(runtime_exports, {
  SpeedInsights: () => SpeedInsights,
  injectSpeedInsights: () => injectSpeedInsights2
});
module.exports = __toCommonJS(runtime_exports);
var import_app = require("nuxt/app");

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
function computeRoute(pathname, pathParams) {
  if (!pathname || !pathParams) {
    return pathname;
  }
  let result = pathname;
  try {
    const entries = Object.entries(pathParams);
    for (const [key, value] of entries) {
      if (!Array.isArray(value)) {
        const matcher = turnValueToRegExp(value);
        if (matcher.test(result)) {
          result = result.replace(matcher, `/[${key}]`);
        }
      }
    }
    for (const [key, value] of entries) {
      if (Array.isArray(value)) {
        const matcher = turnValueToRegExp(value.join("/"));
        if (matcher.test(result)) {
          result = result.replace(matcher, `/[...${key}]`);
        }
      }
    }
    return result;
  } catch {
    return pathname;
  }
}
function turnValueToRegExp(value) {
  return new RegExp(`/${escapeRegExp(value)}(?=[/?#]|$)`);
}
function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
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

// src/vue/create-component.ts
var import_vue = require("vue");
var import_vue_router = require("vue-router");

// src/vue/utils.ts
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

// src/vue/create-component.ts
function createComponent(framework = "vue") {
  return (0, import_vue.defineComponent)({
    props: [
      "dsn",
      "sampleRate",
      "beforeSend",
      "debug",
      "scriptSrc",
      "endpoint"
    ],
    setup(props) {
      const route = (0, import_vue_router.useRoute)();
      const configure = injectSpeedInsights(
        {
          ...Object.fromEntries(
            // trim out undefined values to avoid overriding config values
            Object.entries(props).filter(([_, v]) => v !== void 0)
          ),
          framework,
          basePath: getBasePath()
        },
        getConfigString()
      );
      if (route && configure) {
        const changeRoute = () => {
          configure.setRoute(computeRoute(route.path, route.params));
        };
        changeRoute();
        (0, import_vue.watch)(route, changeRoute);
      }
    },
    // Vue component must have a render function, or a template.
    render() {
      return null;
    }
  });
}

// src/nuxt/runtime/utils.ts
var import_meta2 = {};
function getBasePath2() {
  try {
    return import_meta2.env.VITE_VERCEL_OBSERVABILITY_BASEPATH;
  } catch {
  }
}
function getConfigString2() {
  try {
    return import_meta2.env.VITE_VERCEL_OBSERVABILITY_CLIENT_CONFIG;
  } catch {
  }
}

// src/nuxt/runtime/index.ts
var SpeedInsights = createComponent("nuxt");
function injectSpeedInsights2(props = {}) {
  if (isBrowser()) {
    const router = (0, import_app.useRouter)();
    const route = (0, import_app.useRoute)();
    const speedInsights = injectSpeedInsights(
      {
        ...props,
        route: computeRoute(route.path, route.params),
        framework: "nuxt",
        basePath: getBasePath2()
      },
      getConfigString2()
    );
    router.afterEach((to) => {
      speedInsights == null ? void 0 : speedInsights.setRoute(computeRoute(to.path, to.params));
    });
  }
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  SpeedInsights,
  injectSpeedInsights
});
//# sourceMappingURL=index.js.map