# Harmony Hub - Music Education Interface

## Overview
Music Education Interface is an open-source application released under the Affero GPLv3 license. The app is designed to help students learn the trumpet, providing interactive tools and resources for music education.

## Documentation
Comprehensive documentation is available in the [`documentation`](./documentation) folder. It is automatically generated using the [Compodoc](https://compodoc.app/) tool.

To generate the documentation, run:

```bash
npm run compodoc
```

## Building the App
You can build the app for iOS or Android using Ionic Capacitor:

```bash
ionic capacitor build ios --prod
# or
ionic capacitor build android --prod
```

### Important for iOS Release
When archiving the app for release on iOS, patch the following file:

`ios/App/Pods/Target Support Files/Pods-App/Pods-App-frameworks.sh`

At line 44, replace:
```diff
- source="$(readlink "${source}")"
+ source="$(readlink -f "${source}")"
```

## Version Updates
- In `ios/App/App.xcodeproj/project.pbxproj`, update `CURRENT_PROJECT_VERSION` and `MARKETING_VERSION`.
- In `android/app/build.gradle`, update `versionCode` and `versionName`.

---

## Technical Roadmap & How to Contribute
For the latest technical roadmap, upcoming features, and contribution guidelines, please see:

👉 [Technical Roadmap & Contribution Guide](https://github.com/albertoacquilino/music-education-interface-ionic/issues/35)

- Learn about planned features and improvements
- Find out how you can get involved
- See contribution tips and contact information

Let's build a better music education platform together! 🎶
