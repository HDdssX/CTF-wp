const path = require('path');
module.exports = {
  stories: ['../src/stories/**/*.stories.@(js|jsx)'],
  addons: ['@storybook/addon-essentials'],
  framework: '@storybook/react-webpack5',
  webpackFinal: async (config) => {
    config.module.rules.push({
      test: /\.(js|jsx)$/,
      exclude: /node_modules/,
      use: {
        loader: require.resolve('babel-loader'),
        options: {
          presets: [require.resolve('@babel/preset-react')],
        },
      },
    });
    config.resolve.extensions.push('.jsx');
    return config;
  },
};