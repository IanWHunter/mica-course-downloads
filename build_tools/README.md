# Native course app build recipe

This generic recipe builds the course applications associated with this download
repository. Application source remains private. The owner supplies an authenticated,
encrypted input in a temporary unpublished release; the encryption key is a
short-lived repository secret. Only the generic recipe is committed here.

The workflow uses the standard `windows-2022` and `ubuntu-22.04` runners in this
public repository. It does not run if the repository is private, use larger
runners, upload Actions artifacts, or create Actions caches.

Compiler/test output can quote private source, so detailed logs are encrypted.
Completed app archives and verification reports are returned through the same
unpublished release. The owner verifies them before publishing student downloads
on MIT GitHub, then removes the temporary exchange and encryption secret.

The workflow is manual, runs only in the owner's repository and does not run on
pull requests. MIT credentials and personal GitHub access tokens are not supplied
to the build jobs; their built-in token is scoped to this repository.

References: [standard runner billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions),
[draft release access](https://docs.github.com/en/rest/releases/releases#list-releases),
[authenticated encryption](https://cryptography.io/en/latest/fernet/).
