# Changelog

## [0.2.0](https://github.com/qaz17899/funbot/compare/v0.1.0...v0.2.0) (2025-12-15)


### ✨ Features

* add Action Cats workflow for PR rewards � ([#2](https://github.com/qaz17899/funbot/issues/2)) ([0fcac0f](https://github.com/qaz17899/funbot/commit/0fcac0f461d6c7ad850f5cbb3f2ee6d67c579d00))
* add GitHub Actions workflow to automatically convert TODOs, FIXMEs, and HACKs to issues. ([782624b](https://github.com/qaz17899/funbot/commit/782624b3a2cc4446b85d10e89fbbfbf365470d42))
* Add Renovate configuration for automated dependency updates and Ruff configuration for code linting and formatting. ([ae2440f](https://github.com/qaz17899/funbot/commit/ae2440f1c3ae5f768ed744f1fa02b4f0e64d631a))
* **db:** add Aerich migration system ([#10](https://github.com/qaz17899/funbot/issues/10)) ([87cfbd3](https://github.com/qaz17899/funbot/commit/87cfbd3663a745c514400f1c943bc3adcac60a4c))
* implement dpy-style patterns ([#15](https://github.com/qaz17899/funbot/issues/15)) ([f06902f](https://github.com/qaz17899/funbot/commit/f06902f51dd1b2e4802ad267f96777f9490174bf))
* implement perfect architecture framework ([e0ff6ba](https://github.com/qaz17899/funbot/commit/e0ff6ba363d6f5d30147a83146282e55ab4d6190))
* Initialize new Python project with core files, dependency locking, and release automation. ([674a83f](https://github.com/qaz17899/funbot/commit/674a83fa817ecaa07fbf13e7b237d783713f99e8))
* **party:** move navigation buttons inside container ([283f753](https://github.com/qaz17899/funbot/commit/283f753bbab3a0bf1aa7fa63bd81deda060ca0fe))
* **party:** show breeding status and attack bonus percent ([64cf605](https://github.com/qaz17899/funbot/commit/64cf6052c576e2596224cbb8f8c7ef1d89287fbf))
* **pokemon:** add complete Pokeclicker stats system ([5bdea79](https://github.com/qaz17899/funbot/commit/5bdea79347d0dcff6ded03df4634965a3fb22748))
* **pokemon:** add Pokemon system with Discord Components V2 ([#16](https://github.com/qaz17899/funbot/issues/16)) ([424a730](https://github.com/qaz17899/funbot/commit/424a7305eef122c8c53a37f6582ce2995dcc657c))
* **pokemon:** add QuestLine system, DB models, and reorganize scripts ([281b4f6](https://github.com/qaz17899/funbot/commit/281b4f65675e25f95a23ee59090d5301ca01f8e5))
* **pokemon:** add real-time gym battle system with V2 components ([#24](https://github.com/qaz17899/funbot/issues/24)) ([2d57528](https://github.com/qaz17899/funbot/commit/2d575286372865e7c17b8000d2a8021ca85a273a))
* **pokemon:** add route autocomplete, party pagination, and type standardization ([1dcaeca](https://github.com/qaz17899/funbot/commit/1dcaecac2fe68adac44d51487a1dedf65f921ae4))
* **pokemon:** enhance party UI with statistics display ([c3a5d91](https://github.com/qaz17899/funbot/commit/c3a5d919714aa033df0e2f718b585c5ca8e52758))
* **pokemon:** implement EP gain and statistics tracking ([1517319](https://github.com/qaz17899/funbot/commit/1517319dc4baa2d3c82dfd1daf8b0bacac8e4c8e))
* **pokemon:** implement full hatchery/breeding system ([64ea111](https://github.com/qaz17899/funbot/commit/64ea11155a980fffc80682ceb1ca98f45e35ffe4))
* **pokemon:** 實作地下城系統 ([7c7c123](https://github.com/qaz17899/funbot/commit/7c7c123968a4fd4951a66afd5f53c47a217064b3))
* **queue:** add hatchery queue system ([3e07e17](https://github.com/qaz17899/funbot/commit/3e07e1780e19394544919085e4f11ddf9032d877))
* **shop:** implement complete Pokeball inventory and shop system ([bf1b692](https://github.com/qaz17899/funbot/commit/bf1b6927ac26c5e017b2e20319bd3b4c7442c1fb))
* **shop:** redesign UI with V2 components ([a21c9a6](https://github.com/qaz17899/funbot/commit/a21c9a6e2ea44f40434f5ec93485679fe71711f5))
* **ui:** Add Components V2 module with LayoutView-based components ([#14](https://github.com/qaz17899/funbot/issues/14)) ([2889a7a](https://github.com/qaz17899/funbot/commit/2889a7a05b9ed5e6c84607d1933e9b7da936c9cd))
* **vitamins:** implement vitamin system for breeding ([cf602fe](https://github.com/qaz17899/funbot/commit/cf602fea21155590f60422a4b827956a700eb0ae))


### 🐛 Bug Fixes

* add migration for player_eggs table ([018c4d4](https://github.com/qaz17899/funbot/commit/018c4d499e8a6e9c05f101c81b540f0882b844e0))
* address AI review bugs - ball emoji lookup, batch catch duplicates, masterball fallback ([336ab5b](https://github.com/qaz17899/funbot/commit/336ab5bc273c8c83926e0663f375acc0e395e4a7))
* address all AI code review issues ([e6e3965](https://github.com/qaz17899/funbot/commit/e6e396590f0b3cb4eef0fd4448a4a7069a075c74))
* address PR review issues ([#11](https://github.com/qaz17899/funbot/issues/11)) ([1a08bbb](https://github.com/qaz17899/funbot/commit/1a08bbb81f56c6a93b4d82bbabb42e80e18237a9))
* batch catch stats should accumulate for all catches of same Pokemon ([e010661](https://github.com/qaz17899/funbot/commit/e010661d670125f935daab7c74fe1b326b210b34))
* **hatchery:** exact match Pokeclicker Egg.ts:134-136 hatch formula ([8b76c54](https://github.com/qaz17899/funbot/commit/8b76c54078837a769d6a96bb08702c13ef89c53a))
* **party:** move stats above separator line ([9489916](https://github.com/qaz17899/funbot/commit/94899162a6a15f8d09a06135a96b639c431f0e09))
* **party:** reduce V2 component count by merging TextDisplay ([21754ff](https://github.com/qaz17899/funbot/commit/21754ff806ce3fda07d55788286c175e7dd763bf))
* **pokemon:** add autocomplete for explore command region/route ([cbdf11b](https://github.com/qaz17899/funbot/commit/cbdf11b4a844e2dc1f2e2431ac039119fc8213e6))
* **pokemon:** address code review issues from Sourcery AI ([ce36827](https://github.com/qaz17899/funbot/commit/ce36827cf40edb3931333f6cc86286791ac55011))
* **pokemon:** address Gemini AI code review issues ([65f0997](https://github.com/qaz17899/funbot/commit/65f0997bf4d67896afe85876fa2cccfa61560b59))
* **pokemon:** correct attack calculation to match Pokeclicker exactly ([8f724fe](https://github.com/qaz17899/funbot/commit/8f724fe488b3a4554ec0f8622e928913eddc2db1))
* **pokemon:** correct EVs system to match Pokeclicker exactly ([62a225d](https://github.com/qaz17899/funbot/commit/62a225dc11be6c6849f7b0f0e5f9ba7d153db42a))
* **pokemon:** correct route query field name ([2d6f7ac](https://github.com/qaz17899/funbot/commit/2d6f7acbcf962e061ae9d9b55dbdd49a6d99ee31))
* **pokemon:** use normalized route (order_number) for egg step calculation ([5e63ace](https://github.com/qaz17899/funbot/commit/5e63ace89e0599f6c63a88291640c56703b53580))
* register HatcheryCog and PlayerEgg in module exports ([ef80f04](https://github.com/qaz17899/funbot/commit/ef80f04bbc8bd66a342123e1e091e9df95d07449))
* **shop:** add currency emojis to error messages ([a1b7eaa](https://github.com/qaz17899/funbot/commit/a1b7eaa8dab470c3041ebfcb105707ae42bd459b))
* **shop:** use TYPE_CHECKING for FunBot import ([e77e746](https://github.com/qaz17899/funbot/commit/e77e7467a0cb070846386e6b9f3f202d26f63587))
* **ui:** pokeball select uses custom Discord emoji instead of circles ([c5510da](https://github.com/qaz17899/funbot/commit/c5510da3728ee099cdca2cac5f669e88c6733b6d))
* 修復路線自動補全回傳錯誤值及優化商店UI ([7e8a001](https://github.com/qaz17899/funbot/commit/7e8a0012c0a582ac9cd1fda43f06ea66489d44fb))


### ♻️ Refactoring

* centralize catch logic in CatchService.perform_catch_sequence ([d1e7da5](https://github.com/qaz17899/funbot/commit/d1e7da56a0170833249eebc06b2b3be5a53eea4e))
* centralize UI logic and enum definitions ([51b094d](https://github.com/qaz17899/funbot/commit/51b094df53205da976361ce14ca569ecec951165))
* **cogs:** auto-discover cogs from subdirectories ([eb7ef1b](https://github.com/qaz17899/funbot/commit/eb7ef1ba7902abeb0f53d26a22dcf99a8fdd561f))
* consolidate battle logic and standardize naming ([5b03ac9](https://github.com/qaz17899/funbot/commit/5b03ac9c194e336be554074215bae250e4fd5f6b))
* DRY command sync logic and add missing guild warning ([#12](https://github.com/qaz17899/funbot/issues/12)) ([8fe584d](https://github.com/qaz17899/funbot/commit/8fe584d5219dee1f232b6592523d5601c31425ac))
* eliminate duplicate constants and standardize service interfaces ([4b54deb](https://github.com/qaz17899/funbot/commit/4b54debee578b5b6cf5970c0eb0273ff37f5debb))
* eliminate redundant formulas and standardize naming ([8f132da](https://github.com/qaz17899/funbot/commit/8f132da1e7d7c92d549a09e4fa6a073ff1d9eec3))
* **pokemon:** consolidate cogs into single /pokemon command group ([41bdf17](https://github.com/qaz17899/funbot/commit/41bdf177e8e654667dab2ad347a74a2d8a9f794c))
* separate concerns - remove UI dependencies from Service layer ([e36a138](https://github.com/qaz17899/funbot/commit/e36a13832eaae237fad2c405c40512c397b75ea4))
* standardize HatcheryService to use player_id and eliminate autocomplete duplication ([8f4c5fa](https://github.com/qaz17899/funbot/commit/8f4c5fa209ef01fe96385ff31ad91efb07266199))
* standardize pokemon.py to use player_id consistently ([09a4a76](https://github.com/qaz17899/funbot/commit/09a4a76e1d7e5424775fa310fac55b816b45cd79))
* standardize StarterSelectLayout to use player_id ([d9a01c5](https://github.com/qaz17899/funbot/commit/d9a01c502452ce41465c2111ded696cce10893dc))
* standardize UI utils and eliminate magic strings ([73e868c](https://github.com/qaz17899/funbot/commit/73e868cfa6224e84fa6b96559a325e366fb4f446))
* **ui:** standardize emoji usage with Emoji class and currency emoji ([9586b6b](https://github.com/qaz17899/funbot/commit/9586b6b2b7d6b425af967127ea281867c5414524))
* **ui:** standardize emojis across all pokemon cogs ([bb60584](https://github.com/qaz17899/funbot/commit/bb60584a14d1e844bc0ccbeb8285cd1644eb5456))
* unify autocomplete architecture and eliminate magic numbers ([06b359a](https://github.com/qaz17899/funbot/commit/06b359aaad322e821ed9d3d956bb73867a04a4cf))
* unify service instantiation and naming consistency ([96e13c7](https://github.com/qaz17899/funbot/commit/96e13c7be4ef64c89d406cfaa79f0c1e7b3cbc0a))
* update Route Explore to use centralized CatchService ([7e11695](https://github.com/qaz17899/funbot/commit/7e1169526930d940f1522c22e46d6cd05fde6f7c))


### 📚 Documentation

* add architecture documentation ([#13](https://github.com/qaz17899/funbot/issues/13)) ([b4d4889](https://github.com/qaz17899/funbot/commit/b4d488956090c9e8073312be87f0479fead08a06))
* **pokemon:** add TODO for correct Pokerus trigger migration ([ee32e91](https://github.com/qaz17899/funbot/commit/ee32e9127a426acb5a1c7618f9914985f8c77ce3))
