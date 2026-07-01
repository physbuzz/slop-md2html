class Md2HtmlError(Exception):
    """Base exception for md2html."""


class DirectiveError(Md2HtmlError):
    """Raised when a custom md2html directive cannot be processed."""


class IncludeCycleError(DirectiveError):
    """Raised when @include directives recurse into a cycle."""


class BuildError(Md2HtmlError):
    """Raised when a page build fails."""
