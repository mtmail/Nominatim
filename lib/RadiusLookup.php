<?php

namespace Nominatim;

require_once(CONST_BasePath.'/lib/Result.php');

class RadiusLookup
{
    protected $oDB;
    protected $iLimit = 20;
    protected $iFinalLimit = 10;

    protected $aLangPrefOrderSql = "''";

    public function __construct(&$oDB)
    {
        $this->oDB =& $oDB;
        // $this->oPlaceLookup = new PlaceLookup($this->oDB);
    }

    public function setLimit($iLimit = 10)
    {
        // if ($iLimit > 50) $iLimit = 50;
        if ($iLimit < 1) $iLimit = 1;

        $this->iFinalLimit = $iLimit;
        $this->iLimit = $iLimit + min($iLimit, 10);
    }

    public function lookup($fLat, $fLon, $fRadiusMeters, $bDoInterpolation = false)
    {
        $sPointSQL = 'ST_SetSRID(ST_Point('.$fLon.','.$fLat.'),4326)';

        $sSQL = ' SELECT place_id,';
        $sSQL .= ' ST_Distance('.$sPointSQL.', geometry) as distance';
        $sSQL .= ' FROM placex';
        $sSQL .= ' WHERE ST_DWithin('.$sPointSQL.', geometry, '.$fRadiusMeters.', false)';
        $sSQL .= ' and rank_address > 28';
        $sSQL .= ' and ST_GeometryType(geometry) != \'ST_LineString\'';
        $sSQL .= ' and (name is not null or housenumber is not null)';
        $sSQL .= ' and class not in (\'boundary\')';
        $sSQL .= ' and indexed_status = 0 and linked_place_id is null';
        $sSQL .= ' ORDER BY distance ASC limit '. $this->iFinalLimit;

        if (CONST_Debug) var_dump($sSQL);
        
        $aResults = $this->oDB->getAssoc($sSQL, null, 'Could not find places.');

        return $aResults;
    }
}
