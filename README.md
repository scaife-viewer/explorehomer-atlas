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

Run the `import_versions` script:

```
python manage.py shell -c 'from readhomer_atlas.library.importers import import_versions; import_versions;'
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

Page through a version ten lines at a time:
```
{
  lines(version_Urn: "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2", first:10) {
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

and then the next ten lines after that (using the `endCursor` value for `after` )
```
{
  lines(version_Urn: "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2", first:10, after: "YXJyYXljb25uZWN0aW9uOjk=") {
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

## Translation Alignments

### Load sample data
```
./manage.py loaddata alignment_data
```

### Sample Queries

Get alignment chunks for a given line:
```
{
  lines(version_Urn: "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2", book_Position: 1, position: 8) {
    edges {
      cursor
      node {
        id
        label
        textContent
        alignmentChunks {
          edges {
            node {
              id
              items
              alignment {
                name
              }
            }
          }
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

Get alignment chunks for a given range:
```
{
  alignmentChunks(version_Urn: "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2", start_Book_Position: 1, start_Position: 8) {
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
