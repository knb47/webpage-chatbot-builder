const path = require('path');
const BundleTracker = require('webpack-bundle-tracker');
const webpack = require('webpack');

module.exports = (env, argv) => {
  const isProduction = argv.mode === 'production';
  
  // Debug message
  console.log('Webpack stats will be generated at:', path.join(__dirname, 'webpack-stats.json'));

  return {
    entry: {
      bundle: './backend/ui/react/index.js'  // Named entry point
    },
    output: {
      path: path.resolve(__dirname, 'backend/ui/vanilla/js/bundled_imports/'),
      filename: isProduction ? 'react_bundle.[contenthash].js' : 'react_bundle.js',
      publicPath: isProduction ? 'backend/ui/vanilla/js/bundled_imports/' : 'http://localhost:3000/ui/vanilla/js/bundled_imports/',
    },
    module: {
      rules: [
        {
          test: /\.(js|jsx)$/,
          exclude: /node_modules/,
          use: 'babel-loader',
        },
        {
          test: /\.css$/,
          use: ['style-loader', 'css-loader'],
        },
      ],
    },
    resolve: {
      extensions: ['.js', '.jsx'],
    },
    plugins: [
      new webpack.ProgressPlugin(),
      new BundleTracker({
        path: __dirname,
        filename: 'webpack-stats.json',
        relativePath: true
      })
    ],
    devServer: {
      port: 3000,
      hot: true,
      headers: { 'Access-Control-Allow-Origin': '*' },
      proxy: [{ context: ['/'], target: 'http://localhost:8000', changeOrigin: true }],
      static: {
        directory: path.resolve(__dirname),
        watch: true,
      },
    },
    mode: argv.mode || 'development',
    devtool: isProduction ? false : 'eval-source-map',
  };
};