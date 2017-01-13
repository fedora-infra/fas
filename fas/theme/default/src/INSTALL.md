# Theme development install

## Way of work

- The stylesheet is built over less.
- The frontend lib dependancies are managed via bower.
- The development env is based on gulp. However, it's just for ease, you
  can modify less source and  compile them directly with lessc manually if
  you don't want node.

## How to setup the dev env

Make sure you've got [npm](https://github.com/npm/npm#npm1----node-package-manager)
already installed. Then run the following command to install the dev
dependancies (bower, gulp and so on).

```
make install
``

Read the README.md for usage.
