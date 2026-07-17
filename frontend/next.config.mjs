/** @type {import('next').NextConfig} */
const nextConfig = {
  allowedDevOrigins: [
    'curly-geckos-share.loca.lt',
    'rare-pots-tell.loca.lt',
    '192.168.0.104',
    'localhost'
  ],
};

import bundleAnalyzer from '@next/bundle-analyzer';

const withBundleAnalyzer = bundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
});

export default withBundleAnalyzer(nextConfig);
