# Explore Homer ATLAS

ATLAS implementation for the Scaife "Explore Homer" prototype

This repository is part of the [Scaife Viewer](https://scaife-viewer.org) project, an open-source ecosystem for building rich online reading environments.

## Getting Started

Make sure you are using a virtual environment of some sort (e.g. `virtualenv` or
`pyenv`).

```
pip install -r requirements-dev.txt
```

Populate the database:

```
./manage.py prepare_db
./manage.py loaddata sites
```

Run the Django dev server:
```
./manage.py runserver
```

Browse to http://localhost:8000/.

Create a superuser:

```
./manage.py createsuperuser
```

Browse to `/admin/library/`

## Sample Queries

Retrieve a list of versions.
```
{
  versions {
    edges {
      node {
        id
        urn
        metadata
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

Retrieve the first version.
```
{
  versions(first: 1) {
    edges {
      node {
        metadata
      }
    }
  }
}
```

Retrieve books within a particular version.
```
{
  textParts(urn_Startswith: "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:", rank: 1) {
    edges {
      node {
        ref
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

Retrieve text part by its URN.
```
{
  textParts(urn: "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1") {
    edges {
      node {
        ref
        textContent
      }
    }
  }
}
```

Retrieve a passage by its URN along with relevant metadata.
```
{
  passageTextParts(reference: "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1-2") {
    metadata
    edges {
      node {
        ref
        textContent
      }
    }
  }
}
```

Retrieve lines within a book within a particular version.
```
{
  textParts(urn_Startswith: "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:2.", first: 5) {
    edges {
      node {
        ref
        textContent
      }
    }
  }
}
```

Page through text parts ten at a time.
```
{
  textParts(urn_Startswith: "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:", rank: 2, first: 10) {
    edges {
      cursor
      node {
        id
        ref
        textContent
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

And then the next ten lines after that (use the `endCursor` value for `after`).

```
{
  textParts(urn_Startswith: "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:", rank: 3, first: 10, after: "YXJyYXljb25uZWN0aW9uOjk=") {
    edges {
      cursor
      node {
        id
        label
        textContent
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

Dump an entire `Node` tree rooted by URN and halting at `kind`. For example,
here we serialize all CTS URNs from their `NID` root up to (and including) the
level of `Version` nodes, maintaining the tree structure in the final payload.
```
{
  tree(urn: "urn:cts:", upTo: "version") {
    tree
  }
}
```

## Text Alignments

### Sample Queries

Get text alignment chunks for a given reference:
```
{
  textAlignmentChunks(reference: "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.8") {
    edges {
      cursor
      node {
        id
        citation
        items
        alignment {
          name
        }
      }
    }
  }
}
```

Get a version annotated with text alignment chunks:
```
{
  versions (urn:"urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:") {
    edges {
      node {
        metadata,
        textAlignmentChunks (first:2){
          edges {
            node {
              citation
            }
          }
        }
      }
    }
  }
}
```

## Text Annotations

### Sample Queries

Retrieve text annotations
```
{
  textAnnotations {
    edges {
      node {
        urn
        data
        textParts {
          edges {
            node {
              urn
              textContent
            }
          }
        }
      }
    }
  }
}
```

Retrieve text annotations for a given passage
```
{
  passageTextParts(reference:"urn:cts:greekLit:tlg0012.tlg001.msA:1.1") {
    edges {
      node {
        urn
        textAnnotations {
          edges {
            node {
              urn
              data
            }
          }
        }
      }
    }
  }
}
```

## Tests

Invoke tests via:

```
pytest
```

## Deploying to QA instances

PRs against `develop` will automatically be deployed to Heroku as a ["review app"](https://devcenter.heroku.com/articles/github-integration-review-apps) after tests pass on CircleCI.

The review app for a PR will be deleted when the PR is closed / merged, or after 30 days after no new commits are added to an open PR.
