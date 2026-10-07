# Matchers facilities - JavaScript

## Overview

Matchers utilise some specific elements from MARC bibliographic records to generate a unique string which identifies common records that describe the same instance.

The matchers in this directory are implemented with JavaScript.

Takes input being a MARC-in-JSON string of MARC fields, and returns the matchkey string.

Each component of the matchkey is padded with the underscore character to fill to its field width.

## Matchers implementations

### goldrush

The [js/matchers/goldrush](goldrush) implements the "Gold Rush - Colorado Alliance MARC record match key generation" (specification dated September 2021).

### goldrush2024

The [js/matchers/goldrush2024](goldrush2024) implements the "Gold Rush - Colorado Alliance MARC record match key generation" (specification dated 4 December 2024).

### deepdish

The [js/matchers/deepdish](deepdish) returns an array of matchkeys, utilising the "Gold Rush - Colorado Alliance MARC record match key generation" (specification dated 4 December 2024), and the fields "020 International Standard Book Number (ISBN)" and "022 International Standard Serial Number (ISSN)" and "024 Other Standard Identifier".

### malort

The [js/matchers/malort](malort) creates single record clusters by returning an empty string.

### minitex-test

The [js/matchers/minitex-test](minitex-test) is a copy of goldrush2024 and used just to test the test matcher deployment.

### isxn

The [js/matchers/isxn](isxn) for clustering simply around isbn/issn and allow searching on them via SRU.

### sharevde

The [js/matchers/sharevde](sharevde) for clustering on both 996$9 works and instances URIs.

### shareInsts

The [js/matchers/shareInsts](shareInsts) for clustering on the 996$9 instances URI only.

### shareWorks

The [js/matchers/shareWorks](shareWorks) for clustering on the 996$9 Works URI only.

## Matchers tests of development code

Refer to [development guidelines](../README.md#development-of-matchers)
