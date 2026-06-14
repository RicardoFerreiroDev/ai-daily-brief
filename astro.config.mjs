import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://ricardoferreirodev.github.io',
  base: '/ai-daily-brief',
  integrations: [sitemap()],
});
