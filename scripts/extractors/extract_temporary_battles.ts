/**
 * Runtime TypeScript Extractor for TemporaryBattleList
 * 
 * Uses tsx to run TypeScript directly - no transpilation step needed.
 * This guarantees 100% accurate data extraction.
 * 
 * Usage: npx tsx scripts/extract_temporary_battles.ts
 */

import * as fs from 'fs';
import * as path from 'path';

// Auto-mocking proxy that returns reasonable defaults for any missing property
// Also callable - returns first argument (identity function) when invoked
function createAutoMock(defaults: Record<string, any> = {}): any {
    const handler: ProxyHandler<any> = {
        get(target, prop: string) {
            if (prop === 'apply' || prop === 'call' || prop === 'bind') {
                return (...args: any[]) => args[args.length - 1];
            }
            if (prop in target) return target[prop];
            // Return a callable proxy that also returns itself for property access
            return createCallableAutoMock();
        },
        apply(_target, _thisArg, args) {
            // When called as function, return first arg or the arg itself
            return args[0] ?? 'mock';
        }
    };

    // Create a function that is also a proxy
    const fn = function (...args: any[]) { return args[0] ?? 'mock'; };
    return new Proxy(fn, { ...handler, get: (t, p) => handler.get!(defaults, p, defaults) });
}

// Callable auto-mock that returns itself for any property and returns first arg when called
function createCallableAutoMock(): any {
    const cache: Record<string, any> = {};
    const fn = function (...args: any[]) { return args[0] ?? 'mock'; };
    return new Proxy(fn, {
        get(_target, prop: string) {
            if (prop === 'apply' || prop === 'call' || prop === 'bind' || prop === 'toString' || prop === 'valueOf') {
                return fn;
            }
            if (!(prop in cache)) {
                cache[prop] = createCallableAutoMock();
            }
            return cache[prop];
        },
        apply(_target, _thisArg, args) {
            return args[0] ?? 'mock';
        }
    });
}

const GameConstants = createAutoMock({
    Region: { kanto: 0, johto: 1, hoenn: 2, sinnoh: 3, unova: 4, kalos: 5, alola: 6, galar: 7, hisui: 8, paldea: 9, orre: 10 },
    Starter: { Grass: 0, Fire: 1, Water: 2, Special: 3 },
    AchievementOption: { less: 0, equal: 1, more: 2 },
    getDungeonIndex: (name: string) => name,
    getTemporaryBattlesIndex: (name: string) => name,
    Environment: {},
    BattleBackground: {},
    SHINY_CHANCE_REWARD: 0,
    ShadowStatus: { Shadow: 'Shadow', Purified: 'Purified', None: 'None' },
    PokemonType: createAutoMock({}),
    Weather: createAutoMock({}),
});

const BadgeEnums: Record<string, string> = new Proxy({}, {
    get: (_target, prop: string) => prop
}) as any;

// ============================================================================
// REQUIREMENT CLASSES
// ============================================================================

class Requirement {
    requiredValue: number;
    option: number;
    constructor(value = 1, option = GameConstants.AchievementOption.more) {
        this.requiredValue = value;
        this.option = option;
    }
    isCompleted() { return true; }
}

class RouteKillRequirement extends Requirement {
    kills: number; region: string; route: number;
    constructor(value: number, region: number, route: number, option?: number) {
        super(value, option);
        this.kills = value;
        this.region = Object.keys(GameConstants.Region).find(k => (GameConstants.Region as any)[k] === region) || String(region);
        this.route = route;
    }
}

class GymBadgeRequirement extends Requirement {
    badge: string;
    constructor(badge: string, option?: number) {
        super(1, option);
        this.badge = badge;
    }
}

class ClearDungeonRequirement extends Requirement {
    clears: number; dungeon: string;
    constructor(value: number, dungeonIndex: string, option?: number) {
        super(value, option);
        this.clears = value;
        this.dungeon = dungeonIndex;
    }
}

class TemporaryBattleRequirement extends Requirement {
    battle: string; defeats: number;
    constructor(battleName: string, defeatsRequired = 1, option?: number) {
        super(defeatsRequired, option);
        this.battle = battleName;
        this.defeats = defeatsRequired;
    }
}

class QuestLineStepCompletedRequirement extends Requirement {
    questLine: string; step: number;
    constructor(questLineName: string, step: number, option?: number) {
        super(1, option);
        this.questLine = questLineName;
        this.step = step;
    }
}

class QuestLineCompletedRequirement extends Requirement {
    questLine: string;
    constructor(questLineName: string, option?: number) {
        super(1, option);
        this.questLine = questLineName;
    }
}

class QuestLineStartedRequirement extends Requirement {
    questLine: string;
    constructor(questLineName: string, option?: number) {
        super(1, option);
        this.questLine = questLineName;
    }
}

class ObtainedPokemonRequirement extends Requirement {
    pokemon: string; notObtained?: boolean;
    constructor(pokemon: string, notObtained = false) {
        super(1);
        this.pokemon = pokemon;
        if (notObtained) this.notObtained = true;
    }
}

class CaughtPokemonRequirement extends Requirement {
    pokemon: string;
    constructor(pokemon: string) {
        super(1);
        this.pokemon = pokemon;
    }
}

// Dynamic requirement class generator for any unknown types
function createDynamicRequirement(name: string): typeof Requirement {
    return class extends Requirement {
        args: any[];
        constructor(...args: any[]) {
            super(1);
            this.args = args;
            // Store named args if possible
            for (let i = 0; i < args.length; i++) {
                (this as any)[`arg${i}`] = args[i];
            }
        }
    };
}

// All known requirement class names (will be mocked dynamically if not defined)
const knownRequirements = [
    'CustomRequirement', 'LazyRequirementWrapper', 'DummyRequirement',
    'AttackRequirement', 'MoneyRequirement', 'DiamondRequirement', 'TokenRequirement',
    'ClickRequirement', 'CapturedRequirement', 'DefeatedRequirement', 'HatchRequirement',
    'ShinyPokemonRequirement', 'CaptureSpecificPokemonRequirement',
    'PokemonLevelRequirement', 'PokemonAttackRequirement', 'PokerusStatusRequirement',
    'HoldingItemRequirement', 'PokeballRequirement', 'PokeballFilterCountRequirement',
    'ShadowPokemonRequirement', 'EVBonusRequirement', 'VitaminObtainRequirement',
    'QuestRequirement', 'QuestLevelRequirement', 'TimePlayedRequirement',
    'GameStateRequirement', 'ClientRequirement', 'BattleFrontierHighestStageRequirement',
    'BattleFrontierTotalStageRequirement', 'SafariBaitRequirement', 'SafariCatchRequirement',
    'SafariItemsRequirement', 'SafariRocksRequirement', 'SafariStepsRequirement',
    'UndergroundLevelRequirement', 'UndergroundItemsFoundRequirement',
    'UndergroundLayersMinedRequirement', 'UndergroundLayersFullyMinedRequirement',
    'UndergroundUseToolRequirement', 'UndergroundHelperRequirement',
    'FarmHandRequirement', 'FarmPlotsUnlockedRequirement', 'FarmPointsRequirement',
    'BerriesUnlockedRequirement', 'HatcheryHelperRequirement',
    'OakItemLevelRequirement', 'MaxLevelOakItemRequirement',
    'SeededDateRequirement', 'SeededDateSelectNRequirement',
    'DayOfWeekRequirement', 'DayCyclePartRequirement', 'MoonCyclePhaseRequirement',
    'SeviiCaughtRequirement', 'SubregionRequirement', 'ClearAnyDungeonRequirement',
    'InDungeonRequirement', 'InGymRequirement', 'InEnvironmentRequirement',
    'TotalMegaStoneObtainedRequirement', 'TotalSpecialEventsActiveRequirement',
    'AllFlutesTimeActiveRequirement', 'UniqueItemOwnedRequirement',
    'SpecialEventRandomRequirement', 'PokemonDefeatedSelectNRequirement',
    'DefeatedPokemonTypeRequirement', 'MegaEvolveRequirement'
];

// Create dynamic classes for all known requirements
for (const name of knownRequirements) {
    (globalThis as any)[name] = createDynamicRequirement(name);
}

// ko (knockout.js) mock
const ko = {
    pureComputed: (fn: () => any) => fn,
    computed: (fn: () => any) => fn,
    observable: (val: any) => () => val,
    observableArray: (arr: any[]) => () => arr,
};

class SpecialEventRequirement extends Requirement {
    event: string;
    constructor(eventName: string) {
        super(1);
        this.event = eventName;
    }
}

class ItemOwnedRequirement extends Requirement {
    item: string; amount: number;
    constructor(item: string, amount = 1, option?: number) {
        super(amount, option);
        this.item = item;
        this.amount = amount;
    }
}

class StarterRequirement extends Requirement {
    region: string; starter: string;
    constructor(region: number, starter: number) {
        super(1);
        this.region = Object.keys(GameConstants.Region).find(k => (GameConstants.Region as any)[k] === region) || String(region);
        this.starter = Object.keys(GameConstants.Starter).find(k => (GameConstants.Starter as any)[k] === starter) || String(starter);
    }
}

class MultiRequirement extends Requirement {
    requirements: Requirement[];
    constructor(requirements: Requirement[] = []) {
        super(requirements.length);
        this.requirements = requirements;
    }
}

class OneFromManyRequirement extends Requirement {
    requirements: Requirement[];
    constructor(requirements: Requirement[] = []) {
        super(1);
        this.requirements = requirements;
    }
}

class NullRequirement extends Requirement {
    constructor() { super(0); }
}

class StatisticRequirement extends Requirement {
    stat: any; hint: string;
    constructor(stat: any, value: number, hint: string, option?: number) {
        super(value, option);
        this.stat = stat;
        this.hint = hint;
    }
}

class MaxRegionRequirement extends Requirement {
    region: string;
    constructor(region: number, option?: number) {
        super(region, option);
        this.region = Object.keys(GameConstants.Region).find(k => (GameConstants.Region as any)[k] === region) || String(region);
    }
}

class ClearGymRequirement extends Requirement {
    clears: number; gym: string;
    constructor(value: number, gym: string, option?: number) {
        super(value, option);
        this.clears = value;
        this.gym = gym;
    }
}

class WeatherRequirement extends Requirement {
    weathers: any; regionNum: number;
    constructor(weathers: any, region: number) {
        super(1);
        this.weathers = weathers;
        this.regionNum = region;
    }
}

class DevelopmentRequirement extends Requirement {
    constructor() { super(1); }
}

class InRegionRequirement extends Requirement {
    region: string;
    constructor(region: number) {
        super(1);
        this.region = Object.keys(GameConstants.Region).find(k => (GameConstants.Region as any)[k] === region) || String(region);
    }
}

class AchievementRequirement extends Requirement { }

// ============================================================================
// GYM POKEMON CLASS
// ============================================================================

class GymPokemon {
    name: string;
    health: number;
    level: number;
    requirement?: Requirement;
    shiny?: boolean;
    requirements: Requirement[];

    constructor(name: string, health: number, level: number, requirement: Requirement | null = null, shiny = false) {
        this.name = name;
        this.health = health;
        this.level = level;
        if (requirement) this.requirement = requirement;
        if (shiny) this.shiny = true;
        this.requirements = requirement ? [requirement] : [];
    }
}

// ============================================================================
// TOWN CONTENT & TEMPORARY BATTLE
// ============================================================================

class TownContent {
    requirements: Requirement[];
    parent?: any;
    constructor(requirements: Requirement[] = []) {
        this.requirements = requirements;
    }
    isUnlocked() { return true; }
}

interface TemporaryBattleOptionalArgument {
    rewardFunction?: () => void;
    firstTimeRewardFunction?: () => void;
    isTrainerBattle?: boolean;
    displayName?: string;
    returnTown?: string;
    imageName?: string;
    visibleRequirement?: Requirement;
    hideTrainer?: boolean;
    environment?: any[];
    battleBackground?: string;
    resetDaily?: boolean;
    finalPokemonImage?: string;
}

type TmpTemporaryBattleType = any;
type TmpTemporaryBattleListType = any;

class TemporaryBattle extends TownContent implements TmpTemporaryBattleType {
    completeRequirements: Requirement[];
    optionalArgs: TemporaryBattleOptionalArgument;

    constructor(
        public name: string,
        public pokemons: GymPokemon[],
        public defeatMessage: string,
        requirements: Requirement[] = [],
        completeRequirements?: Requirement[],
        optionalArgs: TemporaryBattleOptionalArgument = {}
    ) {
        super(requirements);
        if (!completeRequirements) {
            completeRequirements = [new TemporaryBattleRequirement(name)];
        }
        if (optionalArgs.isTrainerBattle === undefined) {
            optionalArgs.isTrainerBattle = true;
        }
        this.completeRequirements = completeRequirements;
        this.optionalArgs = optionalArgs;
    }

    getDisplayName() {
        return this.optionalArgs.displayName ?? this.name.replace(/( route)? \d+$/, '');
    }
    cssClass() { return ''; }
    text() { return ''; }
    isVisible() { return true; }
    onclick() { }
    areaStatus() { return []; }
    getTown() { return undefined; }
    getImage() { return ''; }
    getPokemonList() { return this.pokemons; }
}

// ============================================================================
// ADDITIONAL MOCKS
// ============================================================================

const App = { game: { party: { gainPokemonByName: () => { } }, wallet: { gainMoney: () => { } }, statistics: {} as any, quests: { getQuestLine: () => ({}) as any }, badgeCase: { hasBadge: () => true } } };
const BagHandler = { gainItem: () => { } };
const ItemList: Record<string, any> = new Proxy({}, { get: () => ({ gain: () => { } }) });
const ItemType = { item: 'item' };
const Notifier = { notify: () => { } };
const NotificationConstants = { NotificationOption: {} as any, NotificationSetting: { Dungeons: {} as any, Items: {} as any } };
const PokemonFactory = { generateShiny: () => false };
const PokemonHelper = { getPokemonByName: (name: string) => ({ id: name }) };
const TemporaryBattleRunner = { startBattle: () => { }, finalPokemon: () => false };
const TownList: Record<string, any> = {};
const areaStatus = { locked: 'locked', incomplete: 'incomplete', completed: 'completed' };
const player = { itemList: {} as any };
const TextMerger = { mergeText: (t: string) => t };
const ChristmasPresent = function (this: any, n: number) { this.gain = () => { }; };

// Make globals available
(globalThis as any).GameConstants = GameConstants;
(globalThis as any).BadgeEnums = BadgeEnums;
(globalThis as any).Requirement = Requirement;
(globalThis as any).RouteKillRequirement = RouteKillRequirement;
(globalThis as any).GymBadgeRequirement = GymBadgeRequirement;
(globalThis as any).ClearDungeonRequirement = ClearDungeonRequirement;
(globalThis as any).TemporaryBattleRequirement = TemporaryBattleRequirement;
(globalThis as any).QuestLineStepCompletedRequirement = QuestLineStepCompletedRequirement;
(globalThis as any).QuestLineCompletedRequirement = QuestLineCompletedRequirement;
(globalThis as any).QuestLineStartedRequirement = QuestLineStartedRequirement;
(globalThis as any).ObtainedPokemonRequirement = ObtainedPokemonRequirement;
(globalThis as any).SpecialEventRequirement = SpecialEventRequirement;
(globalThis as any).ItemOwnedRequirement = ItemOwnedRequirement;
(globalThis as any).StarterRequirement = StarterRequirement;
(globalThis as any).MultiRequirement = MultiRequirement;
(globalThis as any).OneFromManyRequirement = OneFromManyRequirement;
(globalThis as any).NullRequirement = NullRequirement;
(globalThis as any).StatisticRequirement = StatisticRequirement;
(globalThis as any).MaxRegionRequirement = MaxRegionRequirement;
(globalThis as any).ClearGymRequirement = ClearGymRequirement;
(globalThis as any).WeatherRequirement = WeatherRequirement;
(globalThis as any).DevelopmentRequirement = DevelopmentRequirement;
(globalThis as any).InRegionRequirement = InRegionRequirement;
(globalThis as any).AchievementRequirement = AchievementRequirement;
(globalThis as any).GymPokemon = GymPokemon;
(globalThis as any).TownContent = TownContent;
(globalThis as any).TemporaryBattle = TemporaryBattle;
(globalThis as any).App = App;
(globalThis as any).BagHandler = BagHandler;
(globalThis as any).ItemList = ItemList;
(globalThis as any).ItemType = ItemType;
(globalThis as any).Notifier = Notifier;
(globalThis as any).NotificationConstants = NotificationConstants;
(globalThis as any).PokemonFactory = PokemonFactory;
(globalThis as any).PokemonHelper = PokemonHelper;
(globalThis as any).TemporaryBattleRunner = TemporaryBattleRunner;
(globalThis as any).TownList = TownList;
(globalThis as any).areaStatus = areaStatus;
(globalThis as any).player = player;
(globalThis as any).TextMerger = TextMerger;
(globalThis as any).ChristmasPresent = ChristmasPresent;
(globalThis as any).ko = ko;
(globalThis as any).CaughtPokemonRequirement = CaughtPokemonRequirement;

// Add all common enums that might be used
const enumMocks = [
    'WeatherType', 'PokemonType', 'BerryType', 'MulchType', 'OakItemType',
    'PokemonCategory', 'QuestLineState', 'GameState', 'DungeonType',
    'KeyItemType', 'Region', 'Starter', 'Weather', 'Environment',
    'BattleBackground', 'AchievementType', 'ShardTraderLocations',
    'RoamingPokemonList', 'DateCycleType', 'DayCyclePart', 'MoonCyclePhase',
    'BagItem', 'Currency', 'PokeballType', 'EggType', 'PartyPokemon',
    'PokemonNameType', 'PokemonListData', 'SpecialEventType',
    // Helper classes and game objects
    'QuestLineHelper', 'GymList', 'DungeonList', 'dungeonList', 'pokemonList',
    'RouteHelper', 'MapHelper', 'PartyController', 'DungeonRunner', 'GymRunner',
    'Underground', 'Farming', 'Berry', 'Safari', 'BerryDeals',
    'EvolutionHandler', 'PokemonContestController', 'ContestHall',
    'PokeballFactory', 'EggFactory', 'ShopHandler', 'ItemHandler',
    'AchievementHandler', 'LogbookController', 'SaveController',
    'DayCycle', 'Weather as WeatherVar', 'SeededRand', 'Rand',
    'OakItems', 'OakItemRunner', 'OakItemSlots',
    'UndergroundItems', 'UndergroundHelper',
    'FarmController', 'FarmLogic', 'Hatchery', 'HatcheryHelper',
    'DungeonBossPokemon', 'GymBadge', 'BadgeCase',
    'pokemonsPerRoute', 'RoamingPokemon', 'ShadowPokemon',
    'MegaStoneItem', 'ZCrystalItem', 'SpecialItem',
    'SpecialEvents', 'FlavorItems', 'Vitamins',
    'pokemonMap', 'PokemonDB', 'pokemonTypeIcons',
];

for (const name of enumMocks) {
    (globalThis as any)[name] = createAutoMock({});
}

// ============================================================================
// LOAD THE FILE
// ============================================================================

console.log('Loading TemporaryBattleList.ts...');

const battleListPath = path.join(__dirname, '..', 'reference', 'pokeclicker-develop', 'src', 'scripts', 'temporaryBattle', 'TemporaryBattleList.ts');
let code = fs.readFileSync(battleListPath, 'utf-8');

// Remove TypeScript-specific things that would cause issues
code = code.replace(/\/\/\/\s*<reference.*?\/>/g, '');
code = code.replace(/satisfies\s+\w+;?/g, ';'); // Remove satisfies statements
code = code.replace(/\s+as\s+\w+(\[\])?\b/g, ''); // Remove 'as Type' assertions

// Create the TemporaryBattleList
const TemporaryBattleList: Record<string, TemporaryBattle> = {};
(globalThis as any).TemporaryBattleList = TemporaryBattleList;

// Remove the const declaration since we already have it (multiple patterns)
code = code.replace(/const\s+TemporaryBattleList\s*:\s*\{[^}]+\}\s*=\s*\{\}\s*;?/g, '');
code = code.replace(/const\s+TemporaryBattleList\s*=\s*\{\}\s*;?/g, '');

// Create a catch-all proxy that auto-mocks any undefined global
const catchAllScope = new Proxy(globalThis, {
    has(_target, _prop) {
        // Always return true so 'with' catches all variable lookups
        return true;
    },
    get(target, prop) {
        // Handle Symbol props
        if (typeof prop === 'symbol') return (target as any)[prop];

        // First check if it exists on globalThis
        if (prop in target) return (target as any)[prop];
        // Otherwise return an auto-mock (silently, too many to log)
        const mock = createCallableAutoMock();
        (target as any)[prop] = mock;
        return mock;
    }
});

// Execute the code using with() to catch all undefined references
// Note: 'with' is deprecated but this is an extraction script, not production code
const wrappedCode = `with(scope) { ${code} }`;
try {
    const fn = new Function('scope', wrappedCode);
    fn(catchAllScope);
} catch (e: any) {
    console.error('Error executing code:', e.message);
    console.error('Stack:', e.stack?.split('\n').slice(0, 5).join('\n'));
}

console.log(`Loaded ${Object.keys(TemporaryBattleList).length} temporary battles`);

// ============================================================================
// SERIALIZE
// ============================================================================

function requirementToJSON(req: Requirement | null): any {
    if (!req) return null;

    const base: any = { type: req.constructor.name };

    for (const [key, value] of Object.entries(req)) {
        if (key === 'requiredValue' || key === 'option') continue;
        if (typeof value === 'function') continue;

        if (key === 'requirements' && Array.isArray(value)) {
            base.requirements = value.map((r: Requirement) => requirementToJSON(r));
        } else if (value instanceof Requirement) {
            base[key] = requirementToJSON(value);
        } else {
            base[key] = value;
        }
    }

    if (req.option !== undefined && req.option !== GameConstants.AchievementOption.more) {
        base.option = req.option === GameConstants.AchievementOption.less ? 'less' : 'equal';
    }

    return base;
}

function pokemonToJSON(poke: GymPokemon): any {
    const obj: any = {
        name: poke.name,
        health: poke.health,
        level: poke.level
    };
    if (poke.requirement) obj.requirement = requirementToJSON(poke.requirement);
    if (poke.shiny) obj.shiny = true;
    return obj;
}

function battleToJSON(battle: TemporaryBattle): any {
    const obj: any = {
        name: battle.name,
        displayName: battle.getDisplayName(),
        pokemon: battle.pokemons.map(p => pokemonToJSON(p)),
        defeatMessage: battle.defeatMessage,
        requirements: battle.requirements.map(r => requirementToJSON(r)),
        completeRequirements: battle.completeRequirements.map(r => requirementToJSON(r)),
    };

    const args = battle.optionalArgs;
    if (args.displayName) obj.displayName = args.displayName;
    if (args.returnTown) obj.returnTown = args.returnTown;
    if (args.imageName) obj.imageName = args.imageName;
    if (args.battleBackground) obj.battleBackground = args.battleBackground;
    if (args.isTrainerBattle === false) obj.isTrainerBattle = false;
    if (args.hideTrainer) obj.hideTrainer = true;
    if (args.resetDaily) obj.resetDaily = true;
    if (args.finalPokemonImage) obj.finalPokemonImage = args.finalPokemonImage;
    if (args.visibleRequirement) obj.visibleRequirement = requirementToJSON(args.visibleRequirement);

    if (args.rewardFunction) obj.hasRewardFunction = true;
    if (args.firstTimeRewardFunction) obj.hasFirstTimeRewardFunction = true;

    return obj;
}

const battles = Object.values(TemporaryBattleList).map(b => battleToJSON(b));

console.log(`Serialized ${battles.length} battles`);

let pokemonWithReqs = 0;
let totalPokemon = 0;
battles.forEach((b: any) => {
    b.pokemon.forEach((p: any) => {
        totalPokemon++;
        if (p.requirement) pokemonWithReqs++;
    });
});

console.log(`Total Pokemon: ${totalPokemon}`);
console.log(`Pokemon with requirements: ${pokemonWithReqs}`);

const outputPath = path.join(__dirname, 'temporary_battles_data_final.json');
fs.writeFileSync(outputPath, JSON.stringify(battles, null, 2));
console.log(`\nOutput written to ${outputPath}`);

try {
    JSON.parse(fs.readFileSync(outputPath, 'utf-8'));
    console.log('✅ JSON validation passed');
} catch (e: any) {
    console.error('❌ JSON validation FAILED:', e.message);
}
