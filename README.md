# currentsapi-python
A Python client for the [Currents API](https://currentsapi.services/documents)

##### Provided under MIT License by Zhi Rui Tam.
*Note: this library may be subtly broken or buggy. The code is released under
the MIT License – please take the following message to heart:*
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## General 

This is a Python client library for CurrentsAPI version 1. The functions for the library should mirror the
endpoints from the [documentation](https://currentsapi.services/documents). 

## Installation
Installation for the package can be done via pip.

```commandline
    pip install currentsapi-python
```

## Usage

After installation, import client into your project:

```python
from currentsapi import CurrentsAPI
```

Initialize the client with your API key:

```python
api = CurrentsAPI(api_key='XXXXXXXXXXXXXXXXXXXXXXX')
```

### Endpoints
 
#### Latest News

```python
api.latest_news()
```
#### Query

```python
api.search(keywords='Trump')
```

