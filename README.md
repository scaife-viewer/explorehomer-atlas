# readhomer_atlas

## Getting Started

Make sure you are using a virtual environment of some sort (e.g. `virtualenv` or
`pyenv`).

```
pip install -r requirements-dev.txt
```

Create a PostgreSQL database `readhomer_atlas`

```
createdb readhomer_atlas
```

Populate the database:

```
./manage.py migrate
./manage.py loaddata sites
```

Run the Django dev server:
```
./manage.py runserver
```

Browse to http://localhost:8000/

## Loading data

Create a superuser:

```
./manage.py createsuperuser
```

Add the initial library fixture:

```
./manage.py loaddata library_data
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
  books(version_Urn: "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2") {
    edges {
      node {
        id
        label
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

Retrieve lines within a book within a particular version:
```
{
  lines(version_Urn: "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2", book_Position: 1) {
    edges {
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
