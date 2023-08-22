#!/usr/bin/python3

from osgeo import ogr, osr
import os
import glob
import math

driver = ogr.GetDriverByName('GeoJSON')

def transform(filePath):
    fileName = os.path.basename(filePath)
    baseName = fileName.replace(".geojson", "").replace("_pt", "")

    print(f"Transforming {fileName}")

    # get the input layer
    inDataSet = driver.Open(filePath)
    inLayer = inDataSet.GetLayer()

    inSpatialRef = inLayer.GetSpatialRef()

    # loading projection
    sr = osr.SpatialReference(str(inSpatialRef))

    # detecting EPSG/SRID
    res = sr.AutoIdentifyEPSG()

    srid = sr.GetAuthorityCode(None)

    # input SpatialReference
    inSpatialRef.ImportFromEPSG(int(srid))

    # output SpatialReference
    outSpatialRef = osr.SpatialReference()
    outSpatialRef.ImportFromEPSG(4326)
    outSpatialRef.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

    # create the CoordinateTransformation
    coordTrans = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)

    # create the output layer
    outputShapefile = f"./output/{baseName}.geojson"

    if os.path.exists(outputShapefile):
        driver.DeleteDataSource(outputShapefile)

    outDataSet = driver.CreateDataSource(outputShapefile)
    outLayer = outDataSet.CreateLayer(baseName, geom_type=ogr.wkbPoint)

    # add fields
    inLayerDefn = inLayer.GetLayerDefn()

    for i in range(0, inLayerDefn.GetFieldCount()):
        fieldDefn = inLayerDefn.GetFieldDefn(i)
        outLayer.CreateField(fieldDefn)

    # new field
    radiusField = ogr.FieldDefn("radius", ogr.OFTReal)
    outLayer.CreateField(radiusField)

    # get the output layer's feature definition
    outLayerDefn = outLayer.GetLayerDefn()

    # loop through the input features
    inFeature = inLayer.GetNextFeature()

    while inFeature:
        # get the input geometry
        geom = inFeature.GetGeometryRef()
        # reproject the geometry
        geom.Transform(coordTrans)
        # create a new feature
        outFeature = ogr.Feature(outLayerDefn)
        # set the geometry
        outFeature.SetGeometry(geom)
        # calculate radius from the L_area
        radius = None
        for i in range(0, outLayerDefn.GetFieldCount()):
            fieldName = outLayerDefn.GetFieldDefn(i).GetNameRef()
            if fieldName == "L_area":
                fieldValue = inFeature.GetField(i)
                radius = math.sqrt(fieldValue/3.14159)
        # set the attributes
        for i in range(0, outLayerDefn.GetFieldCount()):
            fieldName = outLayerDefn.GetFieldDefn(i).GetNameRef()
            fieldValue = radius if fieldName == "radius" else inFeature.GetField(i)
            outFeature.SetField(fieldName, fieldValue)
        # add the feature to the shapefile
        outLayer.CreateFeature(outFeature)
        # destroy the features and get the next input feature
        outFeature.Destroy()
        inFeature.Destroy()
        inFeature = inLayer.GetNextFeature()

    # close the shapefiles
    inDataSet.Destroy()
    outDataSet.Destroy()

# main
for file in glob.glob("./input/*_pt.geojson"):
    transform(file)