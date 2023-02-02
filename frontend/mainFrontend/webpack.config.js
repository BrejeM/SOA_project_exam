const HtmlWebpackPlugin = require("html-webpack-plugin");
const ModuleFederationPlugin = require("webpack/lib/container/ModuleFederationPlugin");
const { VueLoaderPlugin } = require('vue-loader');
const path = require('path');
const { dependencies } = require("./package.json");

module.exports = {
  entry: path.resolve(__dirname, './src/index.js'),
  mode: "development",
  devServer: {
    port: 8084,
  },
  module: {
    rules: [
        {
            test: /\.png$/,
            use: {
              loader: 'url-loader',
              options: { limit: 8192 },
            },
          },
        {
            test: /\.vue$/,
            loader: 'vue-loader'
          },
          {
            test: /\.css$/,
            use: [
              'vue-style-loader',
              'css-loader'
            ]
          },
      {
        test: /\.(js|jsx)?$/,
        exclude: /node_modules/,
        use: [
          {
            loader: "babel-loader",
            options: {
              presets: ["@babel/preset-env", "@babel/preset-react"],
            },
          },
        ],
      },
    ],
  },
  plugins: [
    new VueLoaderPlugin(),
    new HtmlWebpackPlugin({
        template: path.resolve(__dirname, './public/index.html'),
        chunks: ['main'],
      }),
    new ModuleFederationPlugin({
      name: "Host",
      remotes: {
        Remote: `Remote@http://localhost:3002/remoteEntry.js`,
      },
      shared: {
        ...dependencies,
        react: {
          singleton: true,
          requiredVersion: dependencies["react"],
        },
        "react-dom": {
          singleton: true,
          requiredVersion: dependencies["react-dom"],
        },
      },
    }),
  ],
  optimization: {
    splitChunks: false,
},

  resolve: {
    extensions: [".js", ".jsx"],
    symlinks: false,
    alias: {
        vue: 'vue/dist/vue.esm-bundler'
      }
  },
  target: "web",
};