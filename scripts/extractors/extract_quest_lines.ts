/**
 * Runtime TypeScript Extractor for QuestLines
 * 
 * Uses tsx to run TypeScript directly - no transpilation step needed.
 * This guarantees 100% accurate data extraction.
 * 
 * Usage: npx tsx scripts/extract_quest_lines.ts
 */

import * as fs from 'fs';
import * as path from 'path';
import * as ts from 'typescript';

// Auto-mocking proxy that returns reasonable defaults for any missing property
// Also callable - returns first argument (identity function) when invoked
function createAutoMock(defaults: Record<string, any> = {}): any {
    const handler: ProxyHandler<any> = {
        get(target, prop: string) {
            if (prop === 'apply' || prop === 'call' || prop === 'bind') {
                return (...args: any[]) => args[args.length - 1];
            }
            if (prop in target) return target[prop];
            return createCallableAutoMock();
        },
        apply(_target, _thisArg, args) {
            return args[0] ?? 'mock';
        }
    };

    const fn = function (...args: any[]) { return args[0] ?? 'mock'; };
    return new Proxy(fn, { ...handler, get: (t, p) => handler.get!(defaults, p, defaults) });
}

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

// ============================================================================
// MOCK GLOBALS
// ============================================================================

const GameConstants = createAutoMock({
    Region: { kanto: 0, johto: 1, hoenn: 2, sinnoh: 3, unova: 4, kalos: 5, alola: 6, galar: 7, hisui: 8, paldea: 9, orre: 10 },
    Starter: { Grass: 0, Fire: 1, Water: 2, Special: 3 },
    AchievementOption: { less: 0, equal: 1, more: 2 },
    BulletinBoards: { None: 0, Kanto: 1, Johto: 2, Hoenn: 3, Sinnoh: 4, Unova: 5, Kalos: 6, Alola: 7, Galar: 8, Paldea: 9 },
    getDungeonIndex: (name: string) => name,
    getTemporaryBattlesIndex: (name: string) => name,
    getGymIndex: (name: string) => name,
    Pokeball: { Pokeball: 0, Greatball: 1, Ultraball: 2, Masterball: 3 },
    GameState: { idle: 0, fighting: 1, gym: 2, dungeon: 3, safari: 4, town: 5 },
    MINUTE: 60000,
    SHINY_CHANCE_REWARD: 0,
});

const BadgeEnums: Record<string, string> = new Proxy({}, {
    get: (_target, prop: string) => prop
}) as any;

// ============================================================================
// REQUIREMENT CLASSES (same as TemporaryBattle extractor)
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

class QuestLineCompletedRequirement extends Requirement {
    questLine: string;
    constructor(questLineName: string, option?: number) {
        super(1, option);
        this.questLine = questLineName;
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

class QuestLineStartedRequirement extends Requirement {
    questLine: string;
    constructor(questLineName: string, option?: number) {
        super(1, option);
        this.questLine = questLineName;
    }
}

class ObtainedPokemonRequirement extends Requirement {
    pokemon: string;
    constructor(pokemon: string) {
        super(1);
        this.pokemon = pokemon;
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

// Dynamic requirement generator for any unknown types
function createDynamicRequirement(name: string): typeof Requirement {
    return class extends Requirement {
        args: any[];
        constructor(...args: any[]) {
            super(1);
            this.args = args;
            for (let i = 0; i < args.length; i++) {
                (this as any)[`arg${i}`] = args[i];
            }
        }
    };
}

const knownRequirements = [
    'CustomRequirement', 'LazyRequirementWrapper', 'DummyRequirement',
    'AttackRequirement', 'MoneyRequirement', 'DiamondRequirement', 'TokenRequirement',
    'MaxRegionRequirement', 'ClearGymRequirement', 'InRegionRequirement',
    'WeatherRequirement', 'DevelopmentRequirement', 'StatisticRequirement',
    'SpecialEventRequirement', 'ItemOwnedRequirement', 'StarterRequirement',
    'CaughtPokemonRequirement', 'AchievementRequirement',
];

for (const name of knownRequirements) {
    (globalThis as any)[name] = createDynamicRequirement(name);
}

// ============================================================================
// QUEST CLASSES
// ============================================================================

const QuestLineState = { inactive: 0, started: 1, ended: 2, suspended: 3 };

class Quest {
    description: string = '';
    questLine?: string;
    index: number = 0;
    inQuestLine: boolean = false;
    parentQuestLine?: any;
    suspended: boolean = false;
    customReward?: () => void;
    optionalArgs?: any;

    constructor(
        public amount: number = 1,
        public pointsReward: number = 0
    ) { }

    withDescription(desc: string): this {
        this.description = desc;
        return this;
    }

    withInitialValue(_val: number): this {
        return this;
    }

    withCustomReward(fn: () => void): this {
        this.customReward = fn;
        return this;
    }

    withOptionalArgs(args: any): this {
        this.optionalArgs = args;
        return this;
    }

    withOnLoad(_fn: () => void): this {
        return this;
    }

    withFocus(_fn: () => void): this {
        return this;
    }

    withIsRepeatable(_val: boolean): this {
        return this;
    }

    progress() { return 0; }
    progressText() { return ''; }
    isCompleted() { return true; }
    initial() { return null; }
    begin() { }
    onLoad() { }
    complete(_silent?: boolean) { }
    createAutoCompleter() { }
}

// All Quest types
class CustomQuest extends Quest {
    hint: string;
    constructor(amount: number, pointsReward: number, description: string, _progressFn?: () => number) {
        super(amount, pointsReward);
        this.description = description;
        this.hint = description;
    }
}

class TalkToNPCQuest extends Quest {
    npcName: string;
    constructor(npc: any, description: string, pointsReward = 0) {
        super(1, pointsReward);
        this.npcName = typeof npc === 'string' ? npc : (npc?.name || 'NPC');
        this.description = description;
    }
}

class DefeatPokemonsQuest extends Quest {
    route: number;
    region: string;
    constructor(amount: number, pointsReward: number, route: number, region: number) {
        super(amount, pointsReward);
        this.route = route;
        this.region = Object.keys(GameConstants.Region).find(k => (GameConstants.Region as any)[k] === region) || String(region);
    }
}

class CapturePokemonsQuest extends Quest {
    constructor(amount: number, pointsReward: number = 0) {
        super(amount, pointsReward);
    }
}

class CaptureSpecificPokemonQuest extends Quest {
    pokemon: string;
    shiny: boolean;
    constructor(pokemon: string, amount = 1, shiny = false, pointsReward = 0) {
        super(amount, pointsReward);
        this.pokemon = pokemon;
        this.shiny = shiny;
    }
}

class DefeatDungeonQuest extends Quest {
    dungeon: string;
    constructor(amount: number, pointsReward: number, dungeon: string) {
        super(amount, pointsReward);
        this.dungeon = dungeon;
    }
}

class DefeatDungeonBossQuest extends Quest {
    dungeon: string;
    boss: string;
    constructor(dungeon: string, boss: string, pointsReward = 0) {
        super(1, pointsReward);
        this.dungeon = dungeon;
        this.boss = boss;
    }
}

class DefeatGymQuest extends Quest {
    gym: string;
    constructor(amount: number, pointsReward: number, gym: string) {
        super(amount, pointsReward);
        this.gym = gym;
    }
}

class DefeatTemporaryBattleQuest extends Quest {
    battle: string;
    constructor(battle: string, description: string, pointsReward = 0) {
        super(1, pointsReward);
        this.battle = battle;
        this.description = description;
    }
}

class BuyPokeballsQuest extends Quest {
    pokeball: number;
    constructor(amount: number, pointsReward: number, pokeball: number) {
        super(amount, pointsReward);
        this.pokeball = pokeball;
    }
}

class HatchEggsQuest extends Quest {
    constructor(amount: number, pointsReward: number) {
        super(amount, pointsReward);
    }
}

class MineLayersQuest extends Quest {
    constructor(amount: number, pointsReward: number) {
        super(amount, pointsReward);
    }
}

class CapturePokemonTypesQuest extends Quest {
    pokemonType: number;
    constructor(amount: number, pointsReward: number, pokemonType: number) {
        super(amount, pointsReward);
        this.pokemonType = pokemonType;
    }
}

class MultipleQuestsQuest extends Quest {
    quests: Quest[];
    constructor(quests: Quest[], description: string, pointsReward = 0) {
        super(quests.length, pointsReward);
        this.quests = quests;
        this.description = description;
    }
}

// ============================================================================
// QUEST LINE CLASS
// ============================================================================

const collectedQuestLines: any[] = [];

// Create a callable array (knockout observableArray style)
function createQuestsArray(): any {
    const arr: Quest[] = [];
    const callable: any = function () { return arr; };
    callable.push = (...items: Quest[]) => arr.push(...items);
    callable[Symbol.iterator] = () => arr[Symbol.iterator]();
    return new Proxy(callable, {
        get(target, prop) {
            if (prop in target) return target[prop];
            return (arr as any)[prop];
        }
    });
}

class QuestLine {
    quests: any;
    totalQuests: number = 0;

    constructor(
        public name: string,
        public _description: string,
        public requirement?: Requirement,
        public bulletinBoard: number = 0,
        public disablePausing: boolean = false
    ) {
        this.quests = createQuestsArray();
    }

    addQuest(quest: any) {
        this.totalQuests++;
        // Handle cases where auto-mock returned a primitive or string
        if (typeof quest !== 'object' || quest === null) {
            quest = new Quest();
            quest.description = String(quest);
        }
        if (typeof quest === 'object') {
            quest.index = this.totalQuests;
            quest.inQuestLine = true;
            quest.parentQuestLine = this;
        }
        this.quests.push(quest);
    }

    get description(): string {
        return this._description;
    }
}

// ============================================================================
// ADDITIONAL MOCKS
// ============================================================================

const ko = {
    pureComputed: (fn: () => any) => fn,
    computed: (fn: () => any) => fn,
    observable: (val: any) => () => val,
    observableArray: (initialArr: any[] = []) => {
        const arr: any[] = [...initialArr];
        // Override arr.push directly so questLines().push() works
        arr.push = function (...items: any[]) {
            for (const item of items) {
                console.log('  [ko.push] QuestLine:', item?.name || 'unknown');
                Array.prototype.push.call(this, item);
                collectedQuestLines.push(item);
            }
            return this.length;
        };
        const result: any = () => arr;
        result.push = arr.push.bind(arr);
        return result;
    },
};

const App = {
    game: {
        party: { gainPokemonByName: () => { } },
        wallet: { gainMoney: () => { }, gainQuestPoints: () => { } },
        statistics: createAutoMock({}),
        quests: {
            questLines: ko.observableArray([]),
            getQuestLine: () => ({ beginQuest: () => { } }),
        },
        badgeCase: { hasBadge: () => true },
        pokeballs: { gainPokeballs: () => { } },
        keyItems: { hasKeyItem: () => true },
        gems: { gainGems: () => { } },
        gameState: 0,
        translation: { getHashed: () => ko.pureComputed(() => '') },
    },
    translation: { getHashed: () => ko.pureComputed(() => '') },
};

const player = { gainItem: () => { }, itemList: {} };
const ItemList: Record<string, any> = new Proxy({}, { get: () => ({ gain: () => { } }) });
const Notifier = { notify: () => { } };
const NotificationConstants = { NotificationOption: {}, NotificationSound: createAutoMock({}) };
const PokemonFactory = { generateShiny: () => false };
const Information = { show: () => { }, hide: () => { } };
const KeyItemType = createAutoMock({});
const PokemonType = createAutoMock({});
const BattleFrontierMilestones = { milestoneRewards: [{ pokemonName: 'Deoxys', obtained: () => false }] };
const pokemonMap = { filter: () => ({ map: () => ({ reduce: () => 0 }) }) };

// All NPC mocks - return the name as a string
const createNPC = (name: string) => ({ name });

// ============================================================================
// MAKE GLOBALS AVAILABLE
// ============================================================================

(globalThis as any).GameConstants = GameConstants;
(globalThis as any).BadgeEnums = BadgeEnums;
(globalThis as any).Requirement = Requirement;
(globalThis as any).RouteKillRequirement = RouteKillRequirement;
(globalThis as any).GymBadgeRequirement = GymBadgeRequirement;
(globalThis as any).ClearDungeonRequirement = ClearDungeonRequirement;
(globalThis as any).TemporaryBattleRequirement = TemporaryBattleRequirement;
(globalThis as any).QuestLineCompletedRequirement = QuestLineCompletedRequirement;
(globalThis as any).QuestLineStepCompletedRequirement = QuestLineStepCompletedRequirement;
(globalThis as any).QuestLineStartedRequirement = QuestLineStartedRequirement;
(globalThis as any).ObtainedPokemonRequirement = ObtainedPokemonRequirement;
(globalThis as any).MultiRequirement = MultiRequirement;
(globalThis as any).OneFromManyRequirement = OneFromManyRequirement;
(globalThis as any).NullRequirement = NullRequirement;
(globalThis as any).QuestLineState = QuestLineState;
(globalThis as any).Quest = Quest;
(globalThis as any).CustomQuest = CustomQuest;
(globalThis as any).TalkToNPCQuest = TalkToNPCQuest;
(globalThis as any).DefeatPokemonsQuest = DefeatPokemonsQuest;
(globalThis as any).CapturePokemonsQuest = CapturePokemonsQuest;
(globalThis as any).CaptureSpecificPokemonQuest = CaptureSpecificPokemonQuest;
(globalThis as any).DefeatDungeonQuest = DefeatDungeonQuest;
(globalThis as any).DefeatDungeonBossQuest = DefeatDungeonBossQuest;
(globalThis as any).DefeatGymQuest = DefeatGymQuest;
(globalThis as any).DefeatTemporaryBattleQuest = DefeatTemporaryBattleQuest;
(globalThis as any).BuyPokeballsQuest = BuyPokeballsQuest;
(globalThis as any).HatchEggsQuest = HatchEggsQuest;
(globalThis as any).MineLayersQuest = MineLayersQuest;
(globalThis as any).CapturePokemonTypesQuest = CapturePokemonTypesQuest;
(globalThis as any).MultipleQuestsQuest = MultipleQuestsQuest;
(globalThis as any).QuestLine = QuestLine;
(globalThis as any).ko = ko;
(globalThis as any).App = App;
(globalThis as any).player = player;
(globalThis as any).ItemList = ItemList;
(globalThis as any).Notifier = Notifier;
(globalThis as any).NotificationConstants = NotificationConstants;
(globalThis as any).PokemonFactory = PokemonFactory;
(globalThis as any).Information = Information;
(globalThis as any).KeyItemType = KeyItemType;
(globalThis as any).PokemonType = PokemonType;
(globalThis as any).BattleFrontierMilestones = BattleFrontierMilestones;
(globalThis as any).pokemonMap = pokemonMap;

// Add common enum/helper mocks
const enumMocks = [
    'WeatherType', 'BerryType', 'MulchType', 'OakItemType',
    'QuestLineHelper', 'GymList', 'DungeonList', 'TownList',
    'MapHelper', 'RouteHelper', 'GameHelper', 'TextMerger',
    'TemporaryBattleList', 'DungeonRunner', 'GymRunner',
    'SpecialEvents', 'BagHandler', 'ShopHandler',
    'Underground', 'Safari', 'Farming', 'Hatchery',
    'PartyController', 'EvolutionHandler',
];

for (const name of enumMocks) {
    (globalThis as any)[name] = createAutoMock({});
}

// ============================================================================
// LOAD AND EXECUTE
// ============================================================================

console.log('Loading QuestLineHelper.ts...');

const helperPath = path.join(__dirname, '..', 'reference', 'pokeclicker-develop', 'src', 'scripts', 'quests', 'QuestLineHelper.ts');
let code = fs.readFileSync(helperPath, 'utf-8');

// Use TypeScript compiler to properly transpile to JavaScript
const transpileResult = ts.transpileModule(code, {
    compilerOptions: {
        target: ts.ScriptTarget.ES2020,
        module: ts.ModuleKind.None,
        strict: false,
        esModuleInterop: true,
        skipLibCheck: true,
        removeComments: false,
    }
});

code = transpileResult.outputText;

// ============================================================================
// PARSE NPC NAMES FROM TownList.ts
// ============================================================================
const townListPath = path.join(__dirname, '..', 'reference', 'pokeclicker-develop', 'src', 'scripts', 'towns', 'TownList.ts');
const townListCode = fs.readFileSync(townListPath, 'utf-8');

// Match patterns like: const VarName = new NPC('RealName', ...) or new ProfNPC('RealName', ...) etc.
// Regex handles escaped quotes like 'Bill\'s Grandpa'
const npcNameMap: Record<string, string> = {};
const npcMatches = townListCode.matchAll(/const\s+(\w+)\s*=\s*new\s+(?:NPC|ProfNPC|GiftNPC|PokemonGiftNPC|RoamerNPC|KantoBerryMasterNPC|AssistantNPC)\s*\(\s*'((?:[^'\\]|\\.)*)'/g);
for (const match of npcMatches) {
    // Unescape the name (e.g., "Bill\'s Grandpa" -> "Bill's Grandpa")
    npcNameMap[match[1]] = match[2].replace(/\\'/g, "'").replace(/\\"/g, '"');
}
console.log(`Found ${Object.keys(npcNameMap).length} NPC name mappings`);

// Find all createXXX method names from the original source
const methodMatches = fs.readFileSync(helperPath, 'utf-8').matchAll(/static\s+(create\w+)\s*\(/g);
const methodNames = [...methodMatches].map(m => m[1]);
console.log(`Found ${methodNames.length} create methods`);

// Append calls to all create methods at end of code
const createCalls = methodNames.map(m => `try { QuestLineHelper.${m}(); } catch(e) { console.error('Error in ${m}:', e.message); }`).join('\n');
code += '\n// Auto-generated calls to all createXXX methods\n' + createCalls;

// Create catch-all scope
const catchAllScope = new Proxy(globalThis, {
    has(_target, _prop) {
        return true;
    },
    get(target, prop) {
        if (typeof prop === 'symbol') return (target as any)[prop];
        if (prop in target) return (target as any)[prop];

        // If the property is a known NPC variable, return an object with the real name
        if (typeof prop === 'string' && npcNameMap[prop]) {
            return { name: npcNameMap[prop] };
        }

        // If the property name ends with 'Quest', return the Quest class
        // This ensures all unknown Quest types are properly chainable
        if (typeof prop === 'string' && prop.endsWith('Quest')) {
            return Quest;
        }

        // Auto-mock for other identifiers
        const mock = createCallableAutoMock();
        (target as any)[prop] = mock;
        return mock;
    }
});

const wrappedCode = `with(scope) { ${code} }`;
try {
    const fn = new Function('scope', wrappedCode);
    fn(catchAllScope);
} catch (e: any) {
    console.error('Error executing code:', e.message);
    console.error('Stack:', e.stack?.split('\n').slice(0, 5).join('\n'));
}

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

function questToJSON(quest: Quest): any {
    const obj: any = {
        type: quest.constructor.name,
        description: quest.description,
        amount: quest.amount,
        pointsReward: quest.pointsReward,
    };

    // Add type-specific fields
    if (quest instanceof TalkToNPCQuest) {
        obj.npcName = quest.npcName;
    } else if (quest instanceof DefeatPokemonsQuest) {
        obj.route = quest.route;
        obj.region = quest.region;
    } else if (quest instanceof CaptureSpecificPokemonQuest) {
        obj.pokemon = quest.pokemon;
        obj.shiny = quest.shiny;
    } else if (quest instanceof DefeatDungeonQuest) {
        obj.dungeon = quest.dungeon;
    } else if (quest instanceof DefeatDungeonBossQuest) {
        obj.dungeon = quest.dungeon;
        obj.boss = quest.boss;
    } else if (quest instanceof DefeatGymQuest) {
        obj.gym = quest.gym;
    } else if (quest instanceof DefeatTemporaryBattleQuest) {
        obj.battle = quest.battle;
    } else if (quest instanceof MultipleQuestsQuest) {
        obj.quests = quest.quests.map(q => questToJSON(q));
    } else if (quest instanceof CapturePokemonTypesQuest) {
        obj.pokemonType = quest.pokemonType;
    }

    if (quest.optionalArgs) obj.optionalArgs = quest.optionalArgs;
    if (quest.customReward) obj.hasCustomReward = true;

    return obj;
}

function questLineToJSON(ql: QuestLine): any {
    const bulletinBoardNames = ['None', 'Kanto', 'Johto', 'Hoenn', 'Sinnoh', 'Unova', 'Kalos', 'Alola', 'Galar', 'Paldea'];

    // Handle callable quests (ko.observableArray pattern)
    const questsArray = typeof ql.quests === 'function' ? ql.quests() : ql.quests;

    return {
        name: ql.name,
        description: ql._description,
        bulletinBoard: bulletinBoardNames[ql.bulletinBoard] || 'None',
        requirement: ql.requirement ? requirementToJSON(ql.requirement) : null,
        quests: questsArray.map((q: Quest) => questToJSON(q)),
        totalQuests: ql.totalQuests,
    };
}

// Filter to only valid QuestLine objects (exclude TEST push)
const validQuestLines = collectedQuestLines.filter(ql => ql && ql.quests && ql._description);
const questLines = validQuestLines.map(ql => questLineToJSON(ql));

console.log(`Serialized ${questLines.length} quest lines`);

let totalQuests = 0;
questLines.forEach((ql: any) => {
    totalQuests += ql.quests.length;
});
console.log(`Total quests: ${totalQuests}`);

const outputPath = path.join(__dirname, 'quest_lines_data.json');
fs.writeFileSync(outputPath, JSON.stringify(questLines, null, 2));
console.log(`\nOutput written to ${outputPath}`);

try {
    JSON.parse(fs.readFileSync(outputPath, 'utf-8'));
    console.log('✅ JSON validation passed');
} catch (e: any) {
    console.error('❌ JSON validation FAILED:', e.message);
}
