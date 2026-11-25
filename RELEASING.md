# Release EbbFlowManager

Pushing a Git tag such as `v1.2.3` triggers the **Create Release** workflow. It
uses the tagged commit's `[UNRELEASED]` notes to publish the FastAPI and Vue
images and create the GitHub release. After a stable release, it opens a
pull request to record those notes in the changelog. [Workflow](.github/workflows/release.yml)

## Prepare the release

Choose a new version based on the changes being released. Use a version such
as `1.2.3` for a stable release or `1.3.0-rc.1` for a prerelease. The changelog
heading and image tags use the version as written. The Git tag adds a `v`.

Keep the notes for the upcoming release in `[UNRELEASED]` in
[CHANGELOG.md](CHANGELOG.md). The workflow creates the dated version section
using the release run's UTC date. If the tagged changelog already has a section
for the version, the workflow uses that section.

The workflow validates the changelog before building. For a patch bump, use
`Fixed` and `Security` sections. A minor bump also allows `Added`, `Changed`,
and `Deprecated`. A major bump also allows `Removed`. Include at least one
bullet under each section heading you use. The version comes from the tag.
[Changelog Reader validation rules](https://github.com/mindsers/changelog-reader-action/blob/v2/src/rules/has-correct-sections.ts)

Merge the release changes and notes into `main`. Confirm that the FastAPI tests,
Vue build, and pre-commit checks passed for the commit you plan to tag. Merge
the previous stable release's changelog PR before tagging the next release.

## Tag and publish

Substitute the prepared version in the example below. Fetch `main` and the tags,
then check that `origin/main` points to the intended commit, its changelog
contains the release notes, and the tag is available. The last command should
print nothing for a new tag.

```sh
release_version=1.2.3
git fetch origin --tags
git log -1 --oneline origin/main
git show origin/main:CHANGELOG.md
git tag --list "v${release_version}"
```

Create an annotated tag on `origin/main` and push that tag to start the workflow.

```sh
git tag -a "v${release_version}" origin/main -m "Release ${release_version}" &&
  git push origin "refs/tags/v${release_version}"
```

## Verify publication

Check the run for your tag in [GitHub Actions](https://github.com/phofmeier/EbbFlowManager/actions/workflows/release.yml).
After it succeeds, confirm that the version and changelog notes appear on the
[Releases page](https://github.com/phofmeier/EbbFlowManager/releases).

| Component               | Versioned image                                       | Stable alias                                       |
| ----------------------- | ----------------------------------------------------- | -------------------------------------------------- |
| FastAPI                 | `ghcr.io/phofmeier/ebbflowmanager:<version>`          | `ghcr.io/phofmeier/ebbflowmanager:latest`          |
| Vue dashboard and Nginx | `ghcr.io/phofmeier/ebbflowmanager:<version>-frontend` | `ghcr.io/phofmeier/ebbflowmanager:latest-frontend` |

Check that both versioned images are available in the registry.

```sh
docker buildx imagetools inspect "ghcr.io/phofmeier/ebbflowmanager:${release_version}"
docker buildx imagetools inspect "ghcr.io/phofmeier/ebbflowmanager:${release_version}-frontend"
```

Stable releases update both aliases. Prereleases publish the versioned images
and appear as prereleases on GitHub. Their notes stay in `[UNRELEASED]` for
the stable release. Deploy both images with the same version. [Compose deployment instructions](example/README.md#use-published-images)

## Merge the changelog pull request

After a stable release, look for **Record release &lt;version&gt; in changelog**.
It moves the published entries into the dated section and keeps any entries
added after the tag under `[UNRELEASED]`. If GitHub asks you to approve the PR
workflow runs, approve them from the pull request page. Merge the PR once its
required checks pass. [GitHub workflow approvals](https://docs.github.com/en/actions/concepts/security/github_token#when-github_token-triggers-workflow-runs)

If the run fails, open the failed step in GitHub Actions. For a transient
failure, rerun the failed job. Rerun a stable release only while it is still
the newest stable version, because the workflow updates both stable aliases.
If the tagged source or changelog needs a correction before publication,
prepare a new version on the corrected commit. If a published entry was edited
on `main` after the tag and the changelog job reports a conflict, reconcile the
notes in a changelog PR so the published text goes into the version section and
any new notes stay under `[UNRELEASED]`.
