# JavaScript facilities

Table of contents:

<!-- $GH_FOLIO/okapi/doc/md2toc -l 1 -h 4 README.md -->
* [Matchers](#matchers)
* [Transformers](#transformers)
    * [999 subfield definitions](#999-subfield-definitions)
        * [999 10 (source holdings record)](#999-10-source-holdings-record)
        * [999 11 (library items)](#999-11-library-items)
        * [999 12 (online items)](#999-12-online-items)
        * [999 13 (vendor entries)](#999-13-vendor-entries)
* [Development of matchers](#development-of-matchers)
    * [Overview](#overview)
    * [Matcher names are restricted](#matcher-names-are-restricted)
    * [Management of branches and pools](#management-of-branches-and-pools)
        * [One pool per git branch](#one-pool-per-git-branch)
        * [Pool identifier and matcher names](#pool-identifier-and-matcher-names)
        * [A pool has one or more matchers](#a-pool-has-one-or-more-matchers)
        * [Remove old pools](#remove-old-pools)
        * [Replace a pool](#replace-a-pool)
        * [Compare pools](#compare-pools)
    * [Configure text editor with .editorconfig](#configure-text-editor-with-editorconfig)
    * [Verify matchers development](#verify-matchers-development)
        * [biome-check](#biome-check)
        * [biome-check-write](#biome-check-write)
        * [Conduct tests](#conduct-tests)
* [GitHub Actions Workflows](#github-actions-workflows)
    * [Workflow biome-check](#workflow-biome-check)
    * [Workflow verify-matcher](#workflow-verify-matcher)
    * [Workflow schedule-deployment](#workflow-schedule-deployment)

# Matchers

Matchers utilise some specific elements from MARC bibliographic records to generate a unique string (the matchkey) which identifies common records that describe the same instance.

The various matchers implementations are explained at [js/matchers](matchers).

Refer also to Reservoir operations documentation about [server configuration](https://github.com/indexdata/reservoir/blob/master/docs/ops/configure.md) of matchers and pools.

The development and deployment of matchers is [explained](#development-of-matchers) below.

# Transformers

A basic example transformer is provided at [transformers](transformers) which
collects MARC fields from all member records and creates field `999_10` for each with: sourceId, localId and globalId.

## 999 subfield definitions

### 999 10 (source holdings record)
```
{
  "i": "clusterId",
  "l": "localId",
  "s": "sourceId",
  "m": "matchKey"
}
```

### 999 11 (library items)
```
{
  "a": "location",
  "b": "barcode",
  "c": "callNumber",
  "d": "callNumberType",
  "g": "copy",
  "i": "institutionName",
  "k": "numberOfPieces",
  "l": "localId",
  "n": "enumeration",
  "p": "policy",
  "s": "sourceId",
  "t": "type",
  "u": "chronology",
  "v": "volume",
  "w": "yearCaption",
  "x": "itemMaterialType",
  "y": "itemId"
}
```

### 999 12 (online items)
```
{
  "i": "instutionName",
  "l": "localId",
  "s": "sourceId",
  "t": "type",
  "u": "uri",
  "r": "rights",
  "x": "nonPublicNote",
  "z": "publicNote"
}
```

### 999 13 (vendor entries)
```
{
  "a": "fullVendorName",
  "b": "price",
  "c": "currencyCode",
  "e": "priceNote",
  "i": "vendor",
  "j": "countryCode",
  "l": "localId",
  "s": "sourceId",
  "t": "type",
  "z": "availability"
}
```

# Development of matchers

## Overview

The various matchers implementations are explained at [js/matchers](matchers).

Each matcher has its own directory (e.g. [js/matchers/goldrush2024](matchers/goldrush2024)) with a README, and example Reservoir configuration files, and the matcher implementation as a JavaScript module `.mjs` file.

Each matcher has tests in the [js/test](test) directory with a JavaScript module (e.g. [js/test/goldrush2024.mjs](test/goldrush2024.mjs)) and a set of assertions (e.g. [js/test/assertions-goldrush2024.json](test/assertions-goldrush2024.json)) which declare the expected matchkey result for processing each associated example record.

The directory [js/test/records](test/records) holds the MARC JSON records. There can be sub-directories to organise the records. Records can be associated with multiple matchers, so if records are modified then ensure that all of the related assertions are adjusted to suit.

Each matcher is briefly explained in the [js/matchers/README.md](matchers/README.md) with a link to its implementation.

For each matcher there is an entry in the [js/package.json](package.json) file to declare its test to be run using Node.js (e.g. `test-goldrush2024`).

To add a new matcher, follow the structure of an existing matcher.
Also declare it at the [matchers-summary.json](../matchers-summary.json) file.

## Matcher names are restricted

> [!IMPORTANT]
> The matcher names are restricted to alpha-numeric or hyphen characters, and must begin with an alpha character, and must not end with hyphen, and must be longer than two characters.

## Management of branches and pools

Reservoir global records are clustered according to rules expressed in a matcher.

A pool is defined by [one or more matchers](#a-pool-has-one-or-more-matchers).

Use the [schedule-deployment](#workflow-schedule-deployment) Workflow to add or remove a pool.

The deployment will configure the matchers in Reservoir, configure the pool, and then run the initializations process to cluster the records into the pool. A VuFind system is automatically configured to provide search and browse and access facilities. It will be available after about 10 minutes.

The VuFind URL will be of this form: \
`https://${poolId}-pool-vufind.reshare-dev.indexdata.com`

### One pool per git branch

Each git branch has only one associated Reservoir pool.

### Pool identifier and matcher names

The identifier of the pool (poolId) is automatically constructed using the name of the branch. The poolId is restricted (slugified) so that the pool identifier forms a legitimate DNS name for the VuFind instance:

* Non-word characters (including underscore) are translated to a single hyphen.
* Converted to lower-case.
* Truncated to the maximum 45 characters.
* The result is an alpha-numeric hyphenated string.

The matcher names are also restricted to alpha-numeric or hyphen characters, with some other [restrictions](#matcher-names-are-restricted).

### A pool has one or more matchers

Declaring multiple matchers for a pool will create a union of match values. It will have the same effect as combining different matchkey implementations as a single JavaScript file and returning a combined list.

This is a convenience feature to avoid duplicating matcher source-code across multiple JavaScript files.

Reservoir combines the keys returned by all configured matchers before doing the clustering.

### Remove old pools

If a pool is no longer needed, then remove the pool, and then delete the git branch.

### Replace a pool

If a pool is not effective and needs to be replaced, then remove the pool, enhance its matchers, and then add its deployment again.

### Compare pools

Compare pools by further enhancing its matchers: Create a new git branch based on the previous one, modify its matchers, then add the new pool.

## Configure text editor with .editorconfig

Before commencing development work, there is a once-off task to configure the text editor.

There is a [.editorconfig](../.editorconfig) file at the top-level of this repository.
See notes to [Configure your editor](https://dev.folio.org/faqs/how-to-use-editorconfig/).

## Verify matchers development

Do 'npm install' to install and update [Biome](https://biomejs.dev).
The package-lock.json on main branch is updated approximately weekly, and is merged to each branch (so do 'git pull').

See all available "scripts" listed in the [package.json](package.json) file.

Prior to commit, do the following steps.

(Note that [Workflows](#github-workflows-actions) (explained below) will also conduct the checks on changes to relevant files, so it is good to verify locally prior to commit.)

### biome-check

Biome will investigate all relevant JavaScript and JSON files, and will report its findings and explanations.

The Biome configuration is deliberately minimal, but still assists to maintain consistent JavaScript code.

```
npm run biome-check
```

### biome-check-write

By default this will apply all fixes, except those that Biome deems to be "unsafe" to apply automatically.

```
npm run biome-check-write
```

If you are happy to let Biome apply the other fixes, then do this. Otherwise manually apply its suggestions.

```
npm run biome-check-write -- --unsafe
```

### Conduct tests

Ensure that the matcher tests do pass.

There are some sample MARC files in the [js/test/records](test/records) directory.
Each matcher has a set of assertions in the [js/test](test) directory.

For example do:

```
npm run test-goldrush2024
```

# GitHub Actions Workflows

There is a set of [Workflows](https://github.com/indexdata/reservoir-scripts/actions) for development and deployment:

## Workflow biome-check

The [biome-check](https://github.com/indexdata/reservoir-scripts/actions/workflows/biome-check.yml) Workflow will be triggered by any git push modification to JavaScript and JSON files.

See documentation above for the pre-commit local [biome-check](#biome-check) checks and fixes.

## Workflow verify-matcher

The [verify-matcher](https://github.com/indexdata/reservoir-scripts/actions/workflows/verify-matcher.yml) Workflow will be triggered by any git push modification to JavaScript files or JSON files.

See documentation above for the local pre-commit [Conduct tests](#conduct-tests) facilities.

The Workflow will discover which files were modified, determine which matchers are involved, and will run the test for each associated matcher.

Note that there is currently a tiny glitch with this workflow. The first git push for a branch will fail, but subsequent pushes will operate properly. There is a workaround to push an initial branch with no modifications, then push subsequent changes.

## Workflow schedule-deployment

The [schedule-deployment](https://github.com/indexdata/reservoir-scripts/actions/workflows/schedule-deployment.yml) Workflow generates and commits a Kubernetes custom resource for the declared pool.

Other back-room processes will subsequently conduct the deployment of the matchers and the pool.

Understand the [Management of branches and pools](#management-of-branches-and-pools).

When matchers are ready, then select the Workflow and trigger a run via the `workflow_dispatch` event (i.e. select `Run workflow` on the right-hand side).

Specify the branch. Note that `main` branch is not allowed.

For each matcher that is to [form the pool](#a-pool-has-one-or-more-matchers), specify its matcher name. This is a comma-separated list of matchers.
For example `goldrush2024,isxn`

Specify the `action` "add or remove".

The Workflow will determine the git commit SHA for the head of the branch, and will use that to reference the source-code of each matcher via its "Raw" GitHub URL.
