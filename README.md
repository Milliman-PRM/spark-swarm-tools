# Spark Swarm - Making Spark Fast Again

This repository contains tools to enable emergent formation of multi-machine Spark Clusters.

For now, at least the `prm.spark.swarm` module in the [PRM/analytics-pipeline repository](https://indy-github.milliman.com/PRM/analytics-pipeline) is likely also necessary tooling (that is not provided here).

## Deployment

This repository will have continuous deployment; a dedicated Jenkins job will checkout and execute this repository periodically.

## Compatible Jenkins job configuration (i.e. how to swarm)

For a Jenkins job to be swarmable:
  1. The job needs to be configured with the `spark_swarm_master` and `spark_swarm_application` parameters.  Each should default to `none`.
  1. The job's build script should have a section that bypasses the main payload when `spark_swarm_master` is provided and instead calls `python -m prm.spark.swarm`
    * Implicitly, this will require that the `prm` python package is available.

## Branching Strategy

This repository will utilize GitHub flow with continuous deployment via Jenkins.
