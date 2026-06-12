// src/remix/index.tsx
import React from "react";

// src/react/index.tsx
import { useEffect, useRef } from "react";

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

// src/react/utils.ts
function getBasePath() {
  if (typeof process === "undefined" || typeof process.env === "undefined") {
    return void 0;
  }
  return process.env.REACT_APP_VERCEL_OBSERVABILITY_BASEPATH;
}
function getConfigString() {
  if (typeof process === "undefined" || typeof process.env === "undefined") {
    return void 0;
  }
  return process.env.REACT_APP_VERCEL_OBSERVABILITY_CLIENT_CONFIG;
}

// src/react/index.tsx
function SpeedInsights(props) {
  useEffect(() => {
    var _a;
    if (props.beforeSend) {
      (_a = window.si) == null ? void 0 : _a.call(window, "beforeSend", props.beforeSend);
    }
  }, [props.beforeSend]);
  const setScriptRoute = useRef(null);
  useEffect(() => {
    if (!setScriptRoute.current) {
      const script = injectSpeedInsights(
        {
          framework: props.framework ?? "react",
          basePath: props.basePath ?? getBasePath(),
          ...props
        },
        props.configString ?? getConfigString()
      );
      if (script) {
        setScriptRoute.current = script.setRoute;
      }
    }
  }, [props]);
  useEffect(() => {
    if (setScriptRoute.current && props.route) {
      setScriptRoute.current(props.route);
    }
  }, [props.route]);
  return null;
}

// src/remix/utils.ts
import { useLocation, useParams } from "@remix-run/react";
var useRoute = () => {
  const params = useParams();
  const location = useLocation();
  return computeRoute(location.pathname, params);
};
function getBasePath2() {
  try {
    return import.meta.env.VITE_VERCEL_OBSERVABILITY_BASEPATH;
  } catch {
  }
}
function getConfigString2() {
  try {
    return import.meta.env.VITE_VERCEL_OBSERVABILITY_CLIENT_CONFIG;
  } catch {
  }
}

// src/remix/index.tsx
function SpeedInsights2(props) {
  return /* @__PURE__ */ React.createElement(
    SpeedInsights,
    {
      route: useRoute(),
      ...props,
      basePath: getBasePath2(),
      configString: getConfigString2(),
      framework: "remix"
    }
  );
}
export {
  SpeedInsights2 as SpeedInsights
};
//# sourceMappingURL=index.mjs.map