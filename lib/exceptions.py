class RequiredParameterPlansNotProvided(Exception):
    pass


class PlansDictContainedNoPlans(Exception):
    pass


class PlanFileDoesNotExist(Exception):
    pass


class UnknownPlanEncountered(Exception):
    pass


class PlanOmittedByRunSelector(Exception):
    pass


class FilesSectionEmpty(Exception):
    pass


class FilesDictLacksListKey(Exception):
    pass


class NoSudoUserParameterDefined(Exception):
    pass


class MalformedInlineAnsibleSnippet(Exception):
    pass


class UnparseablePlanFile(Exception):
    pass


class DuplicatePlanInRocketMode(Exception):
    pass


class RequiredParameterContainerFilepathStackNotProvided(Exception):
    pass


class RequiredParameterCallDepthNotProvided(Exception):
    pass


class RequiredParameterRunSelectorAffirmativeNotProvided(Exception):
    pass


class IncomprehensiblePlanDict(Exception):
    pass


class RequiredParameterOrderNotDefined(Exception):
    pass