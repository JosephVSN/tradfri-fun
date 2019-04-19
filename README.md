# tradfri-fun

Some simple methods for use with the IKEA tradfri lightbulb series. Utilizes the pytradfri library.

## Getting Started

Follow the instructions on the [pytradfri](https://github.com/ggravlingen/pytradfri) repo to get the library setup.
Once pytradfri and it's requirements are installed, clone this repository and run 

```python
control.py IP [-c|--cycle] [-s|--strobe] [-K key]
```

## Methods

#### Cycle
Does a smooth cycle through a few different preset colours. Time between transitions is roughly done through the STEP constant. 

#### Strobe
Does a "strobe"-esque effect through preset colours.

## License

This project is licensed under the GNU License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* [@ggravlingen](https://github.com/ggravlingen) for the pytradfri library & example code that this script is based on
