# readhomer_atlas

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

Browse to http://localhost:8000/

Create a superuser:

```
./manage.py createsuperuser
```

Browse to `/admin/library/`

## Sample Queries

Retrieve a list of versions
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

Retrieve books within a particular version:
```
{
  textParts(urn_Startswith: "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:", depth: 2) {
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

Retrieve text part by its URN:
```
{
  textParts(urn: "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1") {
    edges {
      node {
        ref
        textContent
        displayFormat
      }
    }
  }
}
```

Retrieve lines within a book within a particular version:
```
{
  textParts(urn_Startswith: "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:2.", first: 5) {
    edges {
      node {
        ref
        textContent
        displayFormat
      }
    }
  }
}
```

Page through text parts ten at a time:
```
{
  textParts(urn_Startswith: "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:", depth:3, first: 10) {
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

```

and then the next ten lines after that (using the `endCursor` value for `after` )
```
{
  textParts(urn_Startswith: "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:", depth:3, first: 10, after: "YXJyYXljb25uZWN0aW9uOjk=") {
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
