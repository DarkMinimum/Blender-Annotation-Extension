
# Changelog

This file contains changelog history. Even though it's reflected in commits here you have short change log story.





## 3.0.0

This release was aimed to refactor depth map part as it was working incorrectly in several cases. Initially, I tried to get advice from community.

- `ADDED` Script that tests Mist and Z-buffer values (as teoretecally they both could be used for depth mesurment)
- `ADDED` UI option and functionality for detailed logging. Shows diffs for each point.
- `CHANGED` Iterating over the depth map as it has anchor point in left-bottom and method calculation returns it left-top format.

3.0.2 `CHANGED` Refactored to separate files
3.0.1 `ADDED` Check for the Z-Buffer Composition set up

## 2.0.0

New revison of the addon was aimed to add filter of the occluded heads. The solution is based on the comparing depth values of particular head and Z-buffer value.

- `ADDED` Generating of the Z-buffer
- `ADDED` UI option for enabling occluded heads filtering

2.0.1 `REMOVED` Generation of the annotation exclusively as it is now depth-map dependent

## 1.0.0

MVP implementation. Adapted code to Blender-addon module.

- 1.4.0 `FIXED` Issue, that same depth map was calculated for batch of renders
- 1.3.0 `CHANGED` Bind Handler for recount of the crowd to OnFrameChange
- 1.2.0 `ADDED` Generation of the annotation exclusively, without rerendering
- 1.1.1 `CHANGED` Script for the visualization of the annotation.
- 1.1.0 `ADDED` Counter of people in camera frame.
- 1.0.1 `ADDED` Filter points out of camera scope.
## Links

- During the changes for release 3.0.0 I created a [ticket for StackOverflow](https://blender.stackexchange.com/questions/324704/z-buffer-map-dosent-reflect-real-distance), but I got to resolve it myself :0
- [@DarkMinimum](https://github.com/DarkMinimum)

