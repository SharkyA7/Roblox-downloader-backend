// src/nuxt/module.ts
import { addPlugin, addTemplate, defineNuxtModule } from "@nuxt/kit";
var module_default = defineNuxtModule({
  meta: {
    name: "@vercel/speed-insights",
    configKey: "speedInsights",
    docs: "https://vercel.com/docs/speed-insights/quickstart"
  },
  setup() {
    const template = addTemplate({
      filename: "vercel-speed-insights.client.ts",
      getContents: () => `
import { injectSpeedInsights } from '@vercel/speed-insights/nuxt/runtime'
import { defineNuxtPlugin } from '#imports'

export default defineNuxtPlugin(() => {
  injectSpeedInsights()
})
`
    });
    addPlugin({
      src: template.dst,
      mode: "client"
    });
  }
});
export {
  module_default as default
};
//# sourceMappingURL=index.mjs.map