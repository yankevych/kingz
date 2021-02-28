import trafaret as t

car = t.Dict({
    t.Key('manufacturer'): t.String(max_length=50),
    t.Key('model'): t.String(max_length=50),
    t.Key('year'): t.Int(gte=1900, lte=2100),
    t.Key('color'): t.String(max_length=50),
    t.Key('vin'): t.String(min_length=17, max_length=17),
})



