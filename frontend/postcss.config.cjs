const plugins = {}
try {
  // only include tailwind if it's installed in the environment
  require.resolve('tailwindcss')
  plugins.tailwindcss = {}
} catch (e) {
  // tailwind not installed — proceed without it for build/test environments
}
try {
  require.resolve('autoprefixer')
  plugins.autoprefixer = {}
} catch (e) {
  // autoprefixer not installed — safe to skip in CI/local builds
}

module.exports = { plugins }
